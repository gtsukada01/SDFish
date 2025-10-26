def parse_boats_page(html: str, date: str, supabase: Client) -> List[Dict]:
    """
    Parse boats.php page using HTML table row parsing (FIXED VERSION)

    NEW: Extracts landing names from HTML <a href="/landings/..."> tags
    instead of unreliable "Fish Counts" headers

    SPEC-010 FR-001: Validates actual report date matches requested date to prevent phantom data

    Args:
        html: Raw HTML from boats.php
        date: Requested date (YYYY-MM-DD)
        supabase: Supabase client for database cross-reference

    Returns:
        List of trip dictionaries

    Raises:
        ParserError: If date header cannot be found
        DateMismatchError: If actual date doesn't match requested date
    """
    # Load all known boats from database for validation
    known_boats = get_all_known_boats(supabase)

    # SPEC-010 FR-001: Source Date Validation
    actual_date = extract_report_date_from_header(html)

    if actual_date is None:
        logger.warning(f"{Fore.YELLOW}⚠️  Could not extract report date from page header")
        logger.warning(f"{Fore.YELLOW}    This may indicate page structure has changed")
        raise ParserError(
            f"Could not parse report date from page header. "
            f"Page structure may have changed. "
            f"Manual inspection required."
        )

    # Validate actual date matches requested date
    if actual_date != date:
        logger.error(f"{Fore.RED}❌ DATE MISMATCH DETECTED")
        logger.error(f"{Fore.RED}   Requested: {date}")
        logger.error(f"{Fore.RED}   Actual:    {actual_date}")
        logger.error(f"{Fore.RED}   → Source may be serving fallback/cached content")
        logger.error(f"{Fore.RED}   → This prevents phantom data injection")

        raise DateMismatchError(
            f"Date mismatch: requested {date}, page shows {actual_date}. "
            f"Source may be serving fallback/cached content for future dates. "
            f"ABORTING to prevent phantom data injection."
        )

    logger.info(f"{Fore.GREEN}✅ Source date validated: {actual_date} matches requested {date}")

    soup = BeautifulSoup(html, 'lxml')
    trips = []

    # NEW APPROACH: Parse HTML table rows directly
    # Find all tables with class="table"
    tables = soup.find_all('table', class_='table')

    # Excluded Northern CA landings
    excluded_landings = ['Avila Beach', 'Santa Barbara', 'Morro Bay']

    for table in tables:
        rows = table.find_all('tr')

        for row in rows:
            tds = row.find_all('td')

            if len(tds) >= 3:  # Boat info, Trip details, Dock totals
                # Extract boat info from first <td>
                boat_td = tds[0]
                links = boat_td.find_all('a')

                if len(links) >= 2:
                    # First link: boat name
                    boat_name = links[0].get_text().strip()

                    # Second link: landing name (contains /landings/)
                    landing_link = links[1]
                    landing_name = landing_link.get_text().strip()
                    landing_href = landing_link.get('href', '')

                    # Skip if not a landing link
                    if '/landings/' not in landing_href:
                        continue

                    # Skip excluded Northern CA landings
                    if any(excluded in landing_name for excluded in excluded_landings):
                        logger.info(f"{Fore.YELLOW}⚠️  Skipping excluded landing: {landing_name}")
                        continue

                    # Check if boat is known in database
                    if boat_name in known_boats:
                        boat_info = known_boats[boat_name]
                        if boat_info['landing_name'] != landing_name and boat_info['landing_name'] != 'Unknown':
                            logger.warning(f"{Fore.YELLOW}⚠️  Landing mismatch for {boat_name}")
                            logger.warning(f"{Fore.YELLOW}    Expected: {boat_info['landing_name']}")
                            logger.warning(f"{Fore.YELLOW}    Found: {landing_name}")
                            # Continue anyway - boats can move
                        logger.info(f"{Fore.YELLOW}🔍 Found boat: {boat_name} (validated against database)")
                    else:
                        logger.warning(f"{Fore.RED}🚨 NEW BOAT DETECTED: {boat_name}")
                        logger.warning(f"{Fore.RED}   Landing: {landing_name}")
                        logger.warning(f"{Fore.RED}   This boat is NOT in the database - will be auto-created")

                    # Extract trip details from second <td>
                    trip_details_html = tds[1].decode_contents()
                    trip_details = trip_details_html.replace('<br/>', '\n').strip()

                    # Parse anglers
                    anglers_match = re.search(r'(\d+)\s+Anglers', trip_details)
                    anglers = int(anglers_match.group(1)) if anglers_match else 0

                    # Extract trip type (everything after "Anglers")
                    trip_type_match = re.search(r'Anglers\s*\n(.+)', trip_details)
                    trip_type = trip_type_match.group(1).strip() if trip_type_match else None

                    if not trip_type:
                        logger.info(f"{Fore.YELLOW}   Incomplete trip data for {boat_name}, skipping")
                        continue

                    # Extract catches from third <td>
                    catches_text = tds[2].get_text().strip()

                    if not catches_text:
                        logger.info(f"{Fore.YELLOW}   No catches data for {boat_name}, skipping")
                        continue

                    # Parse catches
                    catches = parse_species_counts(catches_text)

                    # Normalize trip type
                    normalized_trip_type = normalize_trip_type(trip_type)

                    # Create trip dictionary
                    trip = {
                        'boat_name': boat_name,
                        'landing_name': landing_name,
                        'trip_date': date,
                        'trip_duration': normalized_trip_type,
                        'trip_type': normalized_trip_type,
                        'anglers': anglers,
                        'catches': catches
                    }

                    trips.append(trip)
                    logger.info(f"{Fore.GREEN}✅ Parsed: {boat_name} - {len(catches)} species, {anglers} anglers")

    logger.info(f"{Fore.GREEN}✅ Total trips parsed: {len(trips)}")
    return trips

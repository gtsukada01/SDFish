/**
 * T033: Data Quality Validation Script
 *
 * Validates real Supabase data integrity and schema compliance.
 * Run with: npx tsx scripts/validate-real-data.ts
 */

import { supabase } from '../src/lib/supabase'
import { CatchRecord } from './api/types'

interface ValidationResult {
  passed: number
  failed: number
  warnings: string[]
  errors: string[]
}

async function validateRealData(): Promise<ValidationResult> {
  const result: ValidationResult = {
    passed: 0,
    failed: 0,
    warnings: [],
    errors: []
  }

  console.log('=== T033: DATA QUALITY VALIDATION ===\n')

  // Fetch 100 recent trips for validation
  const { data, error } = await supabase
    .from('trips')
    .select(`
      id,
      trip_date,
      trip_duration,
      anglers,
      boats!inner(id, name, landing_id, landings!inner(id, name)),
      catches!inner(species, count)
    `)
    .order('trip_date', { ascending: false })
    .limit(100)

  if (error) {
    result.errors.push(`Supabase query failed: ${error.message}`)
    result.failed++
    return result
  }

  if (!data || data.length === 0) {
    result.errors.push('No data returned from Supabase')
    result.failed++
    return result
  }

  console.log(`✅ Fetched ${data.length} trips for validation\n`)

  // Validation checks
  let nullAnglers = 0
  let nullDuration = 0
  let emptySpecies = 0
  let invalidDates = 0

  for (const trip of data) {
    // Check required fields
    if (!trip.id) {
      result.errors.push(`Trip missing ID: ${JSON.stringify(trip)}`)
      result.failed++
      continue
    }

    if (!trip.trip_date) {
      result.errors.push(`Trip ${trip.id} missing trip_date`)
      result.failed++
      invalidDates++
      continue
    }

    // Check date is reasonable (2020-2030)
    const tripYear = new Date(trip.trip_date).getFullYear()
    if (tripYear < 2020 || tripYear > 2030) {
      result.warnings.push(`Trip ${trip.id} has unusual year: ${tripYear}`)
    }

    // Check boats foreign key
    if (!trip.boats || !trip.boats.name) {
      result.errors.push(`Trip ${trip.id} missing boat information`)
      result.failed++
      continue
    }

    // Check landings foreign key
    if (!trip.boats.landings || !trip.boats.landings.name) {
      result.errors.push(`Trip ${trip.id} missing landing information`)
      result.failed++
      continue
    }

    // Check catches
    if (!Array.isArray(trip.catches) || trip.catches.length === 0) {
      result.warnings.push(`Trip ${trip.id} has no catches`)
      emptySpecies++
    } else {
      // Validate catch structure
      for (const catchItem of trip.catches) {
        if (!catchItem.species || catchItem.species.trim() === '') {
          result.warnings.push(`Trip ${trip.id} has catch with empty species name`)
        }
        if (typeof catchItem.count !== 'number' || catchItem.count <= 0) {
          result.errors.push(`Trip ${trip.id} has invalid catch count: ${catchItem.count}`)
          result.failed++
        }
      }
    }

    // Track nullable fields
    if (trip.anglers === null || trip.anglers === undefined) {
      nullAnglers++
    }

    if (!trip.trip_duration || trip.trip_duration === '') {
      nullDuration++
    }

    result.passed++
  }

  // Summary
  console.log('=== VALIDATION SUMMARY ===\n')
  console.log(`✅ Passed: ${result.passed}/${data.length} trips`)
  console.log(`❌ Failed: ${result.failed} trips`)
  console.log(`⚠️  Warnings: ${result.warnings.length}\n`)

  console.log('=== DATA QUALITY METRICS ===\n')
  console.log(`Null anglers: ${nullAnglers}/${data.length} (${(nullAnglers/data.length*100).toFixed(1)}%)`)
  console.log(`Null/empty duration: ${nullDuration}/${data.length} (${(nullDuration/data.length*100).toFixed(1)}%)`)
  console.log(`Empty species: ${emptySpecies}/${data.length} (${(emptySpecies/data.length*100).toFixed(1)}%)`)
  console.log(`Invalid dates: ${invalidDates}/${data.length}`)

  // Schema compliance check
  console.log('\n=== SCHEMA COMPLIANCE ===\n')
  const sampleTrip = data[0]
  const transformedRecord: Partial<CatchRecord> = {
    id: sampleTrip.id,
    trip_date: sampleTrip.trip_date,
    boat: sampleTrip.boats.name,
    landing: sampleTrip.boats.landings.name,
    trip_duration_hours: sampleTrip.trip_duration || 0,
    angler_count: sampleTrip.anglers,
    total_fish: sampleTrip.catches.reduce((sum, c) => sum + c.count, 0),
    species_breakdown: sampleTrip.catches.map(c => ({ species: c.species, count: c.count }))
  }

  console.log('✅ Sample transformation successful:')
  console.log(`   Date: ${transformedRecord.trip_date}`)
  console.log(`   Boat: ${transformedRecord.boat}`)
  console.log(`   Landing: ${transformedRecord.landing}`)
  console.log(`   Total Fish: ${transformedRecord.total_fish}`)

  // Display errors and warnings
  if (result.errors.length > 0) {
    console.log('\n=== ERRORS ===\n')
    result.errors.slice(0, 10).forEach(err => console.log(`❌ ${err}`))
    if (result.errors.length > 10) {
      console.log(`... and ${result.errors.length - 10} more errors`)
    }
  }

  if (result.warnings.length > 0 && result.warnings.length <= 5) {
    console.log('\n=== WARNINGS ===\n')
    result.warnings.forEach(warn => console.log(`⚠️  ${warn}`))
  }

  console.log('\n=== T033 VALIDATION COMPLETE ===')

  if (result.failed === 0) {
    console.log('✅ All critical validations passed!')
  } else {
    console.log(`⚠️  ${result.failed} trips failed validation - review errors above`)
  }

  return result
}

// Run validation
validateRealData()
  .then(result => {
    process.exit(result.failed > 0 ? 1 : 0)
  })
  .catch(err => {
    console.error('Validation script error:', err)
    process.exit(1)
  })

#!/usr/bin/env node
import { readFile, writeFile, readdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { compile } from 'json-schema-to-typescript';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const FEATURE_DIR = path.resolve(__dirname, '../specs/001-offshore-analytics-table');
const CONTRACTS_DIR = path.join(FEATURE_DIR, 'contracts');
const API_DIR = path.join(__dirname, 'api');

const SCHEMA_CONFIG = {
  'catch-table': {
    typeName: 'CatchTableResponse',
    mockExport: 'mockCatchTableResponse',
    typeRef: 'CatchTableResponse',
  },
  'summary-metrics': {
    typeName: 'SummaryMetricsResponse',
    mockExport: 'mockSummaryMetricsResponse',
    typeRef: 'SummaryMetricsResponse',
  },
  status: {
    typeName: 'StatusResponse',
    mockExport: 'mockStatusResponse',
    typeRef: 'StatusResponse',
  },
};

const toStableJson = (value) => JSON.stringify(value, null, 2);
const toObjectLiteral = (json) => toStableJson(json).replace(/"([^"\n]+)":/g, '$1:');
const cloneSchema = (schema) => JSON.parse(JSON.stringify(schema));

async function loadContractFiles() {
  const entries = await readdir(CONTRACTS_DIR, { withFileTypes: true });
  const schemaFiles = entries
    .filter((entry) => entry.isFile() && entry.name.endsWith('.schema.json'))
    .map((entry) => entry.name)
    .sort();
  const mockFiles = entries
    .filter((entry) => entry.isFile() && entry.name.endsWith('.mock.json'))
    .map((entry) => entry.name)
    .sort();
  return { schemaFiles, mockFiles };
}

function extractDefinitions(tsSource) {
  const definitions = new Map();
  const order = [];
  const trimmed = tsSource.trim();
  if (!trimmed) return { definitions, order };

  const chunks = trimmed.split(/\n(?=export\s+(?:interface|type)\s+)/g);
  for (const chunk of chunks) {
    const match = chunk.match(/^export\s+(?:interface|type)\s+([A-Za-z0-9_]+)/);
    if (!match) continue;
    const name = match[1];
    if (!definitions.has(name)) {
      definitions.set(name, chunk.trimEnd());
      order.push(name);
    }
  }

  return { definitions, order };
}

function mergeDefinitions(target, order, incoming) {
  for (const name of incoming.order) {
    if (!target.has(name)) {
      target.set(name, incoming.definitions.get(name));
      order.push(name);
    }
  }
}

async function generateTypes(schemaFiles) {
  const definitions = new Map();
  const order = [];
  let statusStateAlias = null;

  for (const schemaFile of schemaFiles) {
    const base = schemaFile.replace('.schema.json', '');
    const config = SCHEMA_CONFIG[base];
    if (!config) {
      console.warn(`Skipping unknown schema: ${schemaFile}`);
      continue;
    }

    const schemaPath = path.join(CONTRACTS_DIR, schemaFile);
    const schema = JSON.parse(await readFile(schemaPath, 'utf8'));
    const schemaClone = cloneSchema(schema);
    schemaClone.title = config.typeName;

    const compiled = await compile(schemaClone, config.typeName, {
      additionalProperties: false,
      bannerComment: '',
      cwd: CONTRACTS_DIR,
    });

    const extracted = extractDefinitions(compiled);

    if (base === 'status') {
      const original = extracted.definitions.get('StatusResponse');
      const enums = schema.properties?.status?.enum;
      if (original && Array.isArray(enums) && enums.length > 0) {
        const union = enums.map((value) => `"${value}"`).join(' | ');
        const adjusted = original.replace(/status:\s*[^;]+;/, 'status: StatusState;');
        extracted.definitions.set('StatusResponse', adjusted.trimEnd());
        statusStateAlias = `export type StatusState = ${union};`;
      }
    }

    mergeDefinitions(definitions, order, extracted);
  }

  let output = `// AUTO-GENERATED - DO NOT EDIT BY HAND\n`;
  output += `// Generated from specs/001-offshore-analytics-table/contracts/*.schema.json\n`;
  output += `// Run: npm run generate:types\n\n`;

  for (const name of order) {
    output += `${definitions.get(name)}\n\n`;
  }

  if (statusStateAlias) {
    output += `${statusStateAlias}\n`;
  }

  return output.trimEnd() + '\n';
}

async function generateMocks(mockFiles) {
  const typesNeeded = new Set();
  let output = `// AUTO-GENERATED - DO NOT EDIT BY HAND\n`;
  output += `// Generated from specs/001-offshore-analytics-table/contracts/*.mock.json\n`;
  output += `// Run: npm run generate:types\n\n`;

  for (const mockFile of mockFiles) {
    const config = SCHEMA_CONFIG[mockFile.replace('.mock.json', '')];
    if (config) {
      typesNeeded.add(config.typeRef);
    }
  }

  if (typesNeeded.size > 0) {
    const imports = Array.from(typesNeeded)
      .sort()
      .map((name) => `  ${name},`)
      .join('\n');
    output += `import {\n${imports}\n} from './types.js';\n\n`;
  }

  for (const mockFile of mockFiles) {
    const base = mockFile.replace('.mock.json', '');
    const config = SCHEMA_CONFIG[base];
    if (!config) {
      console.warn(`Skipping unknown mock: ${mockFile}`);
      continue;
    }
    const mockPath = path.join(CONTRACTS_DIR, mockFile);
    const data = JSON.parse(await readFile(mockPath, 'utf8'));
    output += `export const ${config.mockExport}: ${config.typeRef} = ${toObjectLiteral(data)} as const;\n\n`;
  }

  return output.trimEnd() + '\n';
}

async function main() {
  const { schemaFiles, mockFiles } = await loadContractFiles();
  if (schemaFiles.length === 0) {
    console.error('No schema files found under contracts directory.');
    process.exit(1);
  }

  const typesSource = await generateTypes(schemaFiles);
  const mocksSource = await generateMocks(mockFiles);

  await writeFile(path.join(API_DIR, 'types.ts'), typesSource, 'utf8');
  await writeFile(path.join(API_DIR, 'mocks.ts'), mocksSource, 'utf8');

  console.log('✅ Generated types.ts and mocks.ts');
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});

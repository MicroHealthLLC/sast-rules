import yaml from 'js-yaml';
// ruleid: javascript.js-yaml-unsafe-schema
import { function as jsFunction } from 'js-yaml-js-types';

export function loadAll(text: string) {
  // ruleid: javascript.js-yaml-unsafe-schema
  return yaml.load(text, { schema: yaml.DEFAULT_FULL_SCHEMA });
}

export function withFunctions(text: string) {
  return yaml.load(text, { schema: yaml.DEFAULT_SCHEMA.extend([jsFunction]) });
}

export function safe(text: string) {
  // ok: javascript.js-yaml-unsafe-schema
  return yaml.load(text);
}

export function explicitSafe(text: string) {
  // ok: javascript.js-yaml-unsafe-schema
  return yaml.load(text, { schema: yaml.JSON_SCHEMA });
}

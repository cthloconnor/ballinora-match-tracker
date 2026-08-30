/**
 * Entity id helpers shared by the cards.
 *
 * The integration names every fixture entity as `<domain>.<fixture>_<suffix>`
 * (e.g. `sensor.f1_phase`, `binary_sensor.f1_live`). Given any one of them we
 * can derive the full set for the same fixture.
 */

/** Split an entity id into its domain and fixture id. */
export function splitEntity(entityId) {
  const clean = String(entityId || "").trim();
  const dot = clean.indexOf(".");
  if (dot <= 0) {
    return { domain: "", object: clean, fixture: clean };
  }
  const domain = clean.slice(0, dot);
  const object = clean.slice(dot + 1);
  const underscore = object.lastIndexOf("_");
  return {
    domain,
    object,
    fixture: underscore > 0 ? object.slice(0, underscore) : object,
  };
}

/** Sensor entity id for a suffix of the same fixture as `entityId`. */
export function sensorId(entityId, suffix) {
  const { fixture } = splitEntity(entityId);
  return fixture ? `sensor.${fixture}_${suffix}` : null;
}

/** Binary sensor entity id for a suffix of the same fixture. */
export function binaryId(entityId, suffix) {
  const { fixture } = splitEntity(entityId);
  return fixture ? `binary_sensor.${fixture}_${suffix}` : null;
}

/** Button entity id for a suffix of the same fixture. */
export function buttonId(entityId, suffix) {
  const { fixture } = splitEntity(entityId);
  return fixture ? `button.${fixture}_${suffix}` : null;
}

/** State value (or `undefined`) of an entity, tolerating missing entries. */
export function stateOf(hass, entityId) {
  const entity = hass?.states?.[entityId];
  return entity ? entity.state : undefined;
}

/** Attribute value (or `undefined`) of an entity, tolerating missing entries. */
export function attrOf(hass, entityId) {
  return hass?.states?.[entityId]?.attributes ?? {};
}

/** Convenience: read a sensor's attributes for a derived suffix. */
export function sensorAttrs(hass, entityId, suffix) {
  return attrOf(hass, sensorId(entityId, suffix));
}
/** Purpose: turn an id into a label. Used by: the plugins page and its panels. */
export function title(value: string) {
  return value.replaceAll("-", " ").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

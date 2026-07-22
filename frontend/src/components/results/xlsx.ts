import type { ResultRow, SheetName } from "./types";

const encoder = new TextEncoder();
const crcTable = (() => { const table = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; table[n] = c >>> 0; } return table; })();
const crc32 = (bytes: Uint8Array) => { let crc = 0xffffffff; for (const byte of bytes) crc = crcTable[(crc ^ byte) & 0xff] ^ (crc >>> 8); return (crc ^ 0xffffffff) >>> 0; };
const escapeXml = (value: string) => value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\"/g, "&quot;");
const column = (index: number) => { let result = ""; for (index += 1; index; index = Math.floor((index - 1) / 26)) result = String.fromCharCode(65 + (index - 1) % 26) + result; return result; };

function zip(entries: Array<{ name: string; content: string }>): Blob {
  const files = entries.map((entry) => ({ ...entry, bytes: encoder.encode(entry.content) }));
  const local: Uint8Array[] = [], central: Uint8Array[] = []; let offset = 0;
  const part = (size: number) => new Uint8Array(size);
  const write16 = (target: Uint8Array, at: number, value: number) => { target[at] = value & 255; target[at + 1] = value >>> 8 & 255; };
  const write32 = (target: Uint8Array, at: number, value: number) => { write16(target, at, value); write16(target, at + 2, value >>> 16); };
  for (const file of files) {
    const name = encoder.encode(file.name), crc = crc32(file.bytes), header = part(30 + name.length); write32(header, 0, 0x04034b50); write16(header, 4, 20); write32(header, 14, crc); write32(header, 18, file.bytes.length); write32(header, 22, file.bytes.length); write16(header, 26, name.length); header.set(name, 30); local.push(header, file.bytes);
    const dir = part(46 + name.length); write32(dir, 0, 0x02014b50); write16(dir, 4, 20); write16(dir, 6, 20); write32(dir, 16, crc); write32(dir, 20, file.bytes.length); write32(dir, 24, file.bytes.length); write16(dir, 28, name.length); write32(dir, 42, offset); dir.set(name, 46); central.push(dir); offset += header.length + file.bytes.length;
  }
  const centralSize = central.reduce((sum, item) => sum + item.length, 0), end = part(22); write32(end, 0, 0x06054b50); write16(end, 8, files.length); write16(end, 10, files.length); write32(end, 12, centralSize); write32(end, 16, offset);
  return new Blob([...local, ...central, end], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
}

function worksheet(rows: ResultRow[]): string {
  const headers = [...new Set(rows.flatMap((row) => Object.keys(row)))];
  const cell = (address: string, item: unknown) => item === null || item === undefined ? "" : typeof item === "number" ? `<c r="${address}"><v>${item}</v></c>` : `<c r="${address}" t="inlineStr"><is><t>${escapeXml(String(item))}</t></is></c>`;
  const lines = [headers, ...rows.map((row) => headers.map((header) => row[header] ?? null))];
  return `<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>${lines.map((line, rowIndex) => `<row r="${rowIndex + 1}">${line.map((item, columnIndex) => cell(`${column(columnIndex)}${rowIndex + 1}`, item)).join("")}</row>`).join("")}</sheetData></worksheet>`;
}

export function workbookBlob(rows: Partial<Record<SheetName, ResultRow[]>>, metadata: ResultRow): Blob {
  const sheets = Object.entries(rows).filter(([, values]) => values && values.length) as Array<[SheetName, ResultRow[]]>;
  sheets.push(["run_metadata", [metadata]]);
  const contentTypes = sheets.map((_, index) => `<Override PartName="/xl/worksheets/sheet${index + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>`).join("");
  return zip([
    { name: "[Content_Types].xml", content: `<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>${contentTypes}</Types>` },
    { name: "_rels/.rels", content: `<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>` },
    { name: "xl/workbook.xml", content: `<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>${sheets.map(([name], index) => `<sheet name="${name}" sheetId="${index + 1}" r:id="rId${index + 1}"/>`).join("")}</sheets></workbook>` },
    { name: "xl/_rels/workbook.xml.rels", content: `<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">${sheets.map((_, index) => `<Relationship Id="rId${index + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet${index + 1}.xml"/>`).join("")}</Relationships>` },
    ...sheets.map(([, data], index) => ({ name: `xl/worksheets/sheet${index + 1}.xml`, content: worksheet(data) })),
  ]);
}

declare module "opentype.js" {
  export interface BoundingBox {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
  }
  export interface Path {
    getBoundingBox(): BoundingBox;
    toPathData(decimalPlaces?: number): string;
  }
  export interface Font {
    getPath(text: string, x: number, y: number, fontSize: number): Path;
    getPaths(text: string, x: number, y: number, fontSize: number): Path[];
  }
  export function load(
    url: string,
    callback: (err: Error | null, font: Font | null) => void
  ): void;
}

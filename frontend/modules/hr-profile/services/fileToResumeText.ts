/**
 * 이력서 파일( PDF / TXT ) → 원문 텍스트 추출 (클라이언트 전용)
 */

export async function fileToText(file: File): Promise<string> {
  const ext = (file.name.split(".").pop() ?? "").toLowerCase();
  if (ext === "txt" || ext === "text") {
    return readTextFile(file);
  }
  if (ext === "pdf") {
    return readPdfFile(file);
  }
  throw new Error("PDF 또는 TXT 파일만 지원합니다.");
}

function readTextFile(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve((reader.result as string) ?? "");
    reader.onerror = () => reject(new Error("파일을 읽을 수 없습니다."));
    reader.readAsText(file, "UTF-8");
  });
}

async function readPdfFile(file: File): Promise<string> {
  if (typeof window === "undefined") return "";
  try {
    const pdfjs = await import("pdfjs-dist");
    const pdf = await pdfjs.getDocument({ data: await file.arrayBuffer(), useSystemFonts: true }).promise;
    const numPages = Math.min(pdf.numPages, 5);
    const parts: string[] = [];
    for (let i = 1; i <= numPages; i++) {
      const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    const text = content.items.map((it: { str?: string }) => (it as { str?: string }).str ?? "").join(" ");
      parts.push(text);
    }
    return parts.join("\n\n");
  } catch (e) {
    throw new Error("PDF 내용을 읽을 수 없습니다. TXT로 저장해 업로드해 주세요.");
  }
}

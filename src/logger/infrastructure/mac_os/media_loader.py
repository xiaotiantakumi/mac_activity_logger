import Quartz
import os
from typing import Iterator
from CoreFoundation import CFURLCreateWithFileSystemPath, kCFURLPOSIXPathStyle

class MediaLoader:
    """
    PDFや画像ファイルを読み込み、CGImageRefとして提供するクラス
    """

    def load_images_from_file(self, file_path: str) -> Iterator[Quartz.CGImageRef]:
        """
        ファイルパスから画像を読み込み、CGImageRefをイテレートするジェネレータ
        対応フォーマット: PDF, JPEG, PNG, TIFF, GIF, BMP, ICO 等 (ImageIOがサポートするもの)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # 拡張子で判定 (簡易的)
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        url = CFURLCreateWithFileSystemPath(None, file_path, kCFURLPOSIXPathStyle, False)

        if ext == '.pdf':
            yield from self._load_pdf(url)
        else:
            yield from self._load_image(url)

    def _load_pdf(self, url) -> Iterator[Quartz.CGImageRef]:
        """
        PDFを読み込み、各ページをCGImageに変換してyieldする
        """
        pdf_doc = Quartz.CGPDFDocumentCreateWithURL(url)
        if pdf_doc is None:
            print(f"Failed to open PDF: {url}")
            return

        page_count = Quartz.CGPDFDocumentGetNumberOfPages(pdf_doc)
        
        for i in range(1, page_count + 1): # PDF pages are 1-indexed
            page = Quartz.CGPDFDocumentGetPage(pdf_doc, i)
            if page:
                yield self._render_pdf_page_to_image(page)

    def _render_pdf_page_to_image(self, page) -> Quartz.CGImageRef:
        """
        PDFページをビットマップコンテキストに描画してCGImageを作成
        """
        # ページのサイズを取得 (MediaBox)
        rect = Quartz.CGPDFPageGetBoxRect(page, Quartz.kCGPDFMediaBox)
        width = int(rect.size.width)
        height = int(rect.size.height)

        # デバイスRGB色空間
        color_space = Quartz.CGColorSpaceCreateDeviceRGB()

        # ビットマップコンテキスト作成
        # width, height, bitsPerComponent(8), bytesPerRow(0=auto), colorSpace, bitmapInfo
        context = Quartz.CGBitmapContextCreate(
            None, 
            width, 
            height, 
            8, 
            0, 
            color_space, 
            Quartz.kCGImageAlphaPremultipliedLast | Quartz.kCGBitmapByteOrder32Big
        )

        if context is None:
            # フォールバック: Alphaなしなど試すべきだが、一旦Noneを返す
            return None

        # 背景を白で塗りつぶす (PDFは透過のことがあるため)
        Quartz.CGContextSetRGBFillColor(context, 1.0, 1.0, 1.0, 1.0)
        Quartz.CGContextFillRect(context, rect)

        # PDFページを描画
        Quartz.CGContextDrawPDFPage(context, page)

        # 画像を作成
        image_ref = Quartz.CGBitmapContextCreateImage(context)
        return image_ref

    def _load_image(self, url) -> Iterator[Quartz.CGImageRef]:
        """
        ImageIOを使って画像を読み込む
        """
        # Image Sourceを作成
        source = Quartz.CGImageSourceCreateWithURL(url, None)
        if source is None:
            return

        count = Quartz.CGImageSourceGetCount(source)
        for i in range(count):
            image_ref = Quartz.CGImageSourceCreateImageAtIndex(source, i, None)
            if image_ref:
                yield image_ref

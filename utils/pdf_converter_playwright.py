"""HTML to PDF conversion using Playwright (browser-based).

This module provides browser-based PDF conversion using Playwright,
which offers excellent CSS and JavaScript support.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import tempfile

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright not available. Install with: pip install playwright && playwright install chromium")

logger = logging.getLogger(__name__)


class PlaywrightPDFConverter:
    """Browser-based PDF converter using Playwright."""
    
    def __init__(self):
        """Initialize the PDF converter."""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is required for PDF conversion. Install with: pip install playwright && playwright install chromium")
        
        self.temp_dir = Path(tempfile.gettempdir()) / "report_pdfs"
        self.temp_dir.mkdir(exist_ok=True)
        
        logger.info("Playwright PDF converter initialized successfully")
    
    def html_file_to_pdf_css_size(
        self,
        html_file_path: str,
        output_pdf_path: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Convert HTML file to PDF using CSS page size method (no extra spacing).
        
        Args:
            html_file_path: Path to the HTML file to convert
            output_pdf_path: Optional output path for PDF
            options: Optional PDF generation options
            
        Returns:
            Path to the generated PDF file
        """
        html_path = Path(html_file_path)
        
        if not html_path.exists():
            raise FileNotFoundError(f"HTML file not found: {html_file_path}")
        
        # Generate output path if not provided
        if output_pdf_path is None:
            pdf_filename = html_path.stem + ".pdf"
            output_pdf_path = self.temp_dir / pdf_filename
        else:
            output_pdf_path = Path(output_pdf_path)
            output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"Converting HTML to PDF using CSS page size: {html_file_path} -> {output_pdf_path}")
            
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Navigate to HTML file
                page.goto(f"file://{html_path.absolute()}")
                page.wait_for_load_state('networkidle')
                
                # Get content dimensions
                content_info = page.evaluate('''
                    () => {
                        const body = document.body;
                        return {
                            scrollHeight: body.scrollHeight,
                            scrollWidth: body.scrollWidth,
                            offsetHeight: body.offsetHeight,
                            offsetWidth: body.offsetWidth
                        };
                    }
                ''')
                
                logger.info(f"Content dimensions: {content_info['scrollWidth']}x{content_info['scrollHeight']}px")
                
                # Inject CSS to set exact page size
                page.add_style_tag(content=f'''
                    @page {{
                        size: {content_info['scrollWidth']}px {content_info['scrollHeight']}px;
                        margin: 0;
                    }}
                    
                    html, body {{
                        width: {content_info['scrollWidth']}px !important;
                        height: {content_info['scrollHeight']}px !important;
                        margin: 0 !important;
                        padding: 0 !important;
                        overflow: hidden !important;
                    }}
                    
                    body {{
                        box-sizing: border-box;
                    }}
                ''')
                
                # Wait for CSS to apply
                page.wait_for_timeout(500)
                
                # Default options
                default_options = {
                    'prefer_css_page_size': True,
                    'scale': 1.0,
                    'margin': {'top': '0', 'right': '0', 'bottom': '0', 'left': '0'},
                    'print_background': True,
                    'display_header_footer': False
                }
                
                if options:
                    default_options.update(options)
                
                # Generate PDF with CSS page size
                page.pdf(
                    path=str(output_pdf_path),
                    **default_options
                )
                
                browser.close()
            
            logger.info(f"PDF generated successfully with CSS page size: {output_pdf_path}")
            return str(output_pdf_path)
            
        except Exception as e:
            logger.error(f"Failed to convert HTML to PDF with CSS page size: {e}")
            raise Exception(f"PDF conversion failed: {e}")

    def html_file_to_pdf(
        self, 
        html_file_path: str, 
        output_pdf_path: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        single_page: bool = True
    ) -> str:
        """
        Convert HTML file to PDF using browser rendering with auto-scaling.
        
        Args:
            html_file_path: Path to the HTML file to convert
            output_pdf_path: Optional output path for PDF
            options: Optional PDF generation options
            single_page: If True, auto-scale to fit in single page
            
        Returns:
            Path to the generated PDF file
        """
        html_path = Path(html_file_path)
        
        if not html_path.exists():
            raise FileNotFoundError(f"HTML file not found: {html_file_path}")
        
        # Generate output path if not provided
        if output_pdf_path is None:
            pdf_filename = html_path.stem + ".pdf"
            output_pdf_path = self.temp_dir / pdf_filename
        else:
            output_pdf_path = Path(output_pdf_path)
            output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"Converting HTML to PDF using Playwright: {html_file_path} -> {output_pdf_path}")
            
            with sync_playwright() as playwright:
                # Launch browser
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Navigate to HTML file
                page.goto(f"file://{html_path.absolute()}")
                
                # Wait for page to load completely (including any async content)
                page.wait_for_load_state('networkidle')
                
                # Auto-scale calculation if single_page is True
                scale_factor = 1.0
                if single_page:
                    scale_factor = self._calculate_auto_scale(page)
                    logger.info(f"Auto-calculated scale factor: {scale_factor}")
                
                # Default PDF options with auto-scaling and minimal vertical margins
                default_options = {
                    'format': 'A4',
                    'scale': scale_factor,
                    'margin': {
                        'top': '2mm',      # 최소 여백
                        'right': '5mm',    # 양옆 여백 축소
                        'bottom': '2mm',   # 최소 여백
                        'left': '5mm'      # 양옆 여백 축소
                    },
                    'print_background': True,
                    'prefer_css_page_size': False,  # Let us control the sizing
                    'display_header_footer': False,
                }
                
                if options:
                    # Don't override scale if single_page is enabled
                    if single_page and 'scale' in options:
                        del options['scale']
                    default_options.update(options)
                
                # Generate PDF
                page.pdf(
                    path=str(output_pdf_path),
                    **default_options
                )
                
                browser.close()
            
            logger.info(f"PDF generated successfully: {output_pdf_path}")
            return str(output_pdf_path)
            
        except Exception as e:
            logger.error(f"Failed to convert HTML to PDF: {e}")
            raise Exception(f"PDF conversion failed: {e}")
    
    def _calculate_auto_scale(self, page) -> float:
        """
        Calculate optimal scale factor to fit content in single A4 page.
        
        Args:
            page: Playwright page object
            
        Returns:
            Scale factor (0.1 to 1.0)
        """
        try:
            # Get content dimensions
            content_height = page.evaluate("document.body.scrollHeight")
            content_width = page.evaluate("document.body.scrollWidth")
            
            # A4 dimensions in pixels (at 96 DPI)
            # A4: 210 × 297 mm = 794 × 1123 pixels
            # Minimal margins all around (2mm ≈ 7.5px vertical, 5mm ≈ 19px horizontal)
            a4_width = 794 - 19 * 2  # Subtract horizontal margins (19px each side for 5mm)
            a4_height = 1123 - 8 * 2  # Subtract minimal vertical margins (8px for 2mm)
            
            # Calculate scale factors for both dimensions
            width_scale = a4_width / content_width if content_width > a4_width else 1.0
            height_scale = a4_height / content_height if content_height > a4_height else 1.0
            
            # Use the smaller scale factor to ensure both dimensions fit
            scale_factor = min(width_scale, height_scale)
            
            # Add safety margin (95% of calculated scale)
            scale_factor *= 0.95
            
            # Ensure scale is within reasonable bounds
            scale_factor = max(0.3, min(1.0, scale_factor))
            
            logger.info(f"Content dimensions: {content_width}x{content_height}px")
            logger.info(f"A4 available space: {a4_width}x{a4_height}px")
            logger.info(f"Calculated scale factors - Width: {width_scale:.3f}, Height: {height_scale:.3f}")
            logger.info(f"Final scale factor: {scale_factor:.3f}")
            
            return scale_factor
            
        except Exception as e:
            logger.warning(f"Auto-scale calculation failed, using default scale 0.8: {e}")
            return 0.8
    
    def html_string_to_pdf(
        self, 
        html_content: str, 
        output_pdf_path: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Convert HTML string to PDF.
        
        Args:
            html_content: HTML content as string
            output_pdf_path: Optional output path for PDF
            options: Optional PDF generation options
            
        Returns:
            Path to the generated PDF file
        """
        try:
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_html:
                temp_html.write(html_content)
                temp_html_path = temp_html.name
            
            # Convert to PDF
            pdf_path = self.html_file_to_pdf(
                html_file_path=temp_html_path,
                output_pdf_path=output_pdf_path,
                options=options
            )
            
            # Clean up temporary HTML file
            os.unlink(temp_html_path)
            
            return pdf_path
            
        except Exception as e:
            # Clean up temporary file if it exists
            try:
                if 'temp_html_path' in locals():
                    os.unlink(temp_html_path)
            except:
                pass
            raise


def convert_html_to_pdf_css_size(
    html_file_path: str,
    output_pdf_path: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None
) -> str:
    """
    Convenience function to convert HTML file to PDF using CSS page size method.
    
    Args:
        html_file_path: Path to the HTML file to convert
        output_pdf_path: Optional output path for PDF
        options: Optional PDF generation options
        
    Returns:
        Path to the generated PDF file
    """
    converter = PlaywrightPDFConverter()
    return converter.html_file_to_pdf_css_size(html_file_path, output_pdf_path, options)


def convert_html_to_pdf_playwright(
    html_file_path: str, 
    output_pdf_path: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
    single_page: bool = True
) -> str:
    """
    Convenience function to convert HTML file to PDF using Playwright.
    
    Args:
        html_file_path: Path to the HTML file to convert
        output_pdf_path: Optional output path for PDF
        options: Optional PDF generation options
        single_page: If True, auto-scale to fit in single page
        
    Returns:
        Path to the generated PDF file
    """
    converter = PlaywrightPDFConverter()
    return converter.html_file_to_pdf(html_file_path, output_pdf_path, options, single_page)


def is_playwright_available() -> bool:
    """
    Check if Playwright is available.
    
    Returns:
        True if Playwright is available, False otherwise
    """
    return PLAYWRIGHT_AVAILABLE
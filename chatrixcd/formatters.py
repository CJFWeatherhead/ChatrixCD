"""Message formatting utilities for bot responses."""

import re
import html as html_module
from typing import List, Optional


class MessageFormatter:
    """Handles formatting of bot messages for Matrix."""
    
    @staticmethod
    def markdown_to_html(text: str) -> str:
        """Convert markdown-style formatting to HTML.
        
        Supports:
        - **bold**
        - *italic*
        - `code`
        - [links](url)
        
        Args:
            text: Text with markdown formatting
            
        Returns:
            HTML formatted text
        """
        text = html_module.escape(text)
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
        text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
        text = text.replace('\n', '<br>')
        return text
    
    @staticmethod
    def colorize(text: str, color: str, bg_color: Optional[str] = None) -> str:
        """Apply color formatting to text.
        
        Args:
            text: Text to colorize
            color: Foreground color name
            bg_color: Optional background color name
            
        Returns:
            Formatted text with color span
        """
        style = f'color: {color};'
        if bg_color:
            style += f' background-color: {bg_color};'
        return f'<span style="{style}">{text}</span>'
    
    @staticmethod
    def color_success(text: str) -> str:
        """Format text as success (green)."""
        return MessageFormatter.colorize(text, '#4CAF50')
    
    @staticmethod
    def color_error(text: str) -> str:
        """Format text as error (red)."""
        return MessageFormatter.colorize(text, '#F44336')
    
    @staticmethod
    def color_warning(text: str) -> str:
        """Format text as warning (orange)."""
        return MessageFormatter.colorize(text, '#FF9800')
    
    @staticmethod
    def color_info(text: str) -> str:
        """Format text as info (blue)."""
        return MessageFormatter.colorize(text, '#2196F3')
    
    @staticmethod
    def create_table(headers: List[str], rows: List[List[str]]) -> str:
        """Create an HTML table.
        
        Args:
            headers: List of column headers
            rows: List of row data (each row is a list of cell values)
            
        Returns:
            HTML table string
        """
        table_html = '<table style="border-collapse: collapse; width: 100%;">\n'
        table_html += '  <thead>\n    <tr>'
        for header in headers:
            table_html += f'<th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2;">{html_module.escape(str(header))}</th>'
        table_html += '</tr>\n  </thead>\n  <tbody>\n'
        
        for row in rows:
            table_html += '    <tr>'
            for cell in row:
                table_html += f'<td style="border: 1px solid #ddd; padding: 8px;">{html_module.escape(str(cell))}</td>'
            table_html += '</tr>\n'
        
        table_html += '  </tbody>\n</table>'
        return table_html
    
    @staticmethod
    def format_description(description: str, max_length: int = 100) -> str:
        """Format and truncate description text.
        
        Args:
            description: Description text to format
            max_length: Maximum length before truncation
            
        Returns:
            Formatted description, possibly truncated with ellipsis
        """
        if not description or description.strip() == "":
            return "<em>No description</em>"
        
        description = description.strip()
        if len(description) > max_length:
            return html_module.escape(description[:max_length] + "...")
        return html_module.escape(description)


class ANSIFormatter:
    """Handles conversion of ANSI escape codes to HTML."""
    
    # ANSI color code mappings
    ANSI_COLORS = {
        '30': '#000000',  # Black
        '31': '#CD3131',  # Red
        '32': '#0DBC79',  # Green
        '33': '#E5E510',  # Yellow
        '34': '#2472C8',  # Blue
        '35': '#BC3FBC',  # Magenta
        '36': '#11A8CD',  # Cyan
        '37': '#E5E5E5',  # White
        '90': '#666666',  # Bright Black (Gray)
        '91': '#F14C4C',  # Bright Red
        '92': '#23D18B',  # Bright Green
        '93': '#F5F543',  # Bright Yellow
        '94': '#3B8EEA',  # Bright Blue
        '95': '#D670D6',  # Bright Magenta
        '96': '#29B8DB',  # Bright Cyan
        '97': '#FFFFFF',  # Bright White
    }
    
    @staticmethod
    def ansi_to_html(text: str) -> str:
        """Convert ANSI escape codes to HTML with color spans.
        
        Args:
            text: Text containing ANSI escape codes
            
        Returns:
            HTML with color spans
        """
        text = html_module.escape(text)
        ansi_pattern = re.compile(r'\033\[([0-9;]+)m')
        
        result = []
        last_end = 0
        open_spans = 0
        
        for match in ansi_pattern.finditer(text):
            result.append(text[last_end:match.start()])
            codes = match.group(1).split(';')
            
            if '0' in codes or not codes:
                for _ in range(open_spans):
                    result.append('</span>')
                open_spans = 0
            else:
                for code in codes:
                    if code in ANSIFormatter.ANSI_COLORS:
                        color = ANSIFormatter.ANSI_COLORS[code]
                        result.append(f'<span style="color: {color};">')
                        open_spans += 1
            
            last_end = match.end()
        
        result.append(text[last_end:])
        
        for _ in range(open_spans):
            result.append('</span>')
        
        return ''.join(result)
    
    @staticmethod
    def ansi_to_html_for_pre(text: str) -> str:
        """Convert ANSI codes for use in <pre> tags.
        
        Args:
            text: Text with ANSI codes
            
        Returns:
            Text with ANSI codes converted to HTML, safe for <pre>
        """
        text = re.sub(r'\033\[[0-9;]+m', '', text)
        return html_module.escape(text)
    
    @staticmethod
    def format_task_logs(raw_logs: str) -> str:
        """Format task logs with special handling for Ansible/Terraform output.
        
        Args:
            raw_logs: Raw log text
            
        Returns:
            Formatted log text with preserved structure
        """
        if not raw_logs or not raw_logs.strip():
            return "<em>No logs available yet</em>"
        
        lines = raw_logs.split('\n')
        formatted_lines = []
        
        for line in lines:
            if line.strip().startswith('TASK [') or line.strip().startswith('PLAY ['):
                formatted_lines.append(f'<strong>{html_module.escape(line)}</strong>')
            elif 'fatal:' in line.lower() or 'error:' in line.lower():
                formatted_lines.append(f'<span style="color: #F44336;">{html_module.escape(line)}</span>')
            elif 'changed:' in line.lower() or 'ok:' in line.lower():
                formatted_lines.append(f'<span style="color: #4CAF50;">{html_module.escape(line)}</span>')
            elif 'skipping:' in line.lower():
                formatted_lines.append(f'<span style="color: #FF9800;">{html_module.escape(line)}</span>')
            else:
                formatted_lines.append(html_module.escape(line))
        
        return '<br>'.join(formatted_lines)
    
    @staticmethod
    def format_task_logs_html(raw_logs: str) -> str:
        """Format task logs to HTML with enhanced formatting.
        
        Args:
            raw_logs: Raw log text
            
        Returns:
            HTML formatted logs with color and structure
        """
        if not raw_logs or not raw_logs.strip():
            return "<em>No logs available yet</em>"
        
        formatted = ANSIFormatter.format_task_logs(raw_logs)
        return f'<pre style="background-color: #1e1e1e; color: #d4d4d4; padding: 10px; border-radius: 5px; overflow-x: auto; font-family: \'Courier New\', monospace; font-size: 12px;">{formatted}</pre>'

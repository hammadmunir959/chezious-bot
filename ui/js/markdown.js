/**
 * Markdown rendering utility
 * Converts markdown to HTML for bot responses
 */

function renderMarkdown(text) {
    if (!text) return '';

    // Normalize line endings
    text = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

    const lines = text.split('\n');
    let html = '';
    let state = {
        inList: false,
        listType: null,
        inCodeBlock: false,
        inTable: false,
        inParagraph: false,
        tableAlignments: []
    };

    const closeParagraph = () => {
        if (state.inParagraph) {
            html += '</p>\n';
            state.inParagraph = false;
        }
    };

    const closeList = () => {
        if (state.inList) {
            html += `</${state.listType}>\n`;
            state.inList = false;
            state.listType = null;
        }
    };

    const closeTable = () => {
        if (state.inTable) {
            html += '</tbody></table></div>\n';
            state.inTable = false;
        }
    };

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();

        // --- 1. Code Blocks ---
        if (trimmed.startsWith('```')) {
            closeParagraph();
            closeList();
            closeTable();

            if (state.inCodeBlock) {
                html += '</code></pre>\n';
                state.inCodeBlock = false;
            } else {
                const lang = trimmed.slice(3).trim();
                html += `<pre><code class="language-${lang}">`;
                state.inCodeBlock = true;
            }
            continue;
        }

        if (state.inCodeBlock) {
            html += escapeHtml(line) + '\n';
            continue;
        }

        // --- 2. Headings ---
        const h3Match = trimmed.match(/^### (.+)$/);
        const h2Match = trimmed.match(/^## (.+)$/);
        const h1Match = trimmed.match(/^# (.+)$/);

        if (h3Match || h2Match || h1Match) {
            closeParagraph();
            closeList();
            closeTable();

            if (h3Match) html += `<h3>${parseInline(h3Match[1])}</h3>\n`;
            else if (h2Match) html += `<h2>${parseInline(h2Match[1])}</h2>\n`;
            else if (h1Match) html += `<h1>${parseInline(h1Match[1])}</h1>\n`;
            continue;
        }

        // --- 3. Horizontal Rule ---
        if (trimmed.match(/^[\-\*_]{3,}$/)) {
            closeParagraph();
            closeList();
            closeTable();
            html += '<hr>\n';
            continue;
        }

        // --- 4. Blockquotes ---
        if (trimmed.startsWith('> ')) {
            closeParagraph();
            closeList();
            closeTable();
            html += `<blockquote>${parseInline(trimmed.slice(2))}</blockquote>\n`;
            continue;
        }

        // --- 5. Lists ---
        const unorderedMatch = line.match(/^\s*[\-\*\+]\s+(.+)$/);
        const orderedMatch = line.match(/^\s*\d+\.\s+(.+)$/);

        if (unorderedMatch || orderedMatch) {
            closeParagraph();
            closeTable();

            if (unorderedMatch) {
                if (!state.inList || state.listType !== 'ul') {
                    closeList();
                    html += '<ul>\n';
                    state.inList = true;
                    state.listType = 'ul';
                }
                html += `<li>${parseInline(unorderedMatch[1])}</li>\n`;
            } else {
                if (!state.inList || state.listType !== 'ol') {
                    closeList();
                    html += '<ol>\n';
                    state.inList = true;
                    state.listType = 'ol';
                }
                html += `<li>${parseInline(orderedMatch[1])}</li>\n`;
            }
            continue;
        }

        // --- 6. Tables ---
        // --- 6. Tables ---
        // Loose table detection: Must start with |
        if (trimmed.startsWith('|')) {
            // Also check for separator row pattern to confirm table start if not already in table
            // But we can be generous if already in table

            // Split by pipe
            // If the last character is NOT a pipe, the last element is content.
            // If the last character IS a pipe, the last element is empty string (ignore).
            let cells = trimmed.split('|');

            // Remove first empty element (before first pipe)
            if (cells.length > 0 && cells[0].trim() === '') {
                cells.shift();
            }

            // Remove last empty element (after last pipe) IF the line ends with pipe
            if (trimmed.endsWith('|') && cells.length > 0 && cells[cells.length - 1].trim() === '') {
                cells.pop();
            }

            cells = cells.map(c => c.trim());

            // Separator check matches |---| or |:---| etc.
            const isSeparator = cells.length > 0 && cells.every(cell => /^[\-:]+$/.test(cell));

            if (!state.inTable) {
                // To start a table, we ideally want a header row followed by a separator.
                // But simplified parser often just looks for structure.
                // Let's require at least one pipe inside (2+ cells) OR follow standard GF
                // For now, if it looks like a table row and we aren't in a table...
                // We might need to look ahead, but that's expensive.
                // Let's assume if it has | and is not a code block, it's a table candidate.
                // To avoid false positives, maybe require at least 2 cells?

                if (!isSeparator && cells.length >= 1) {
                    state.inTable = true;
                    // We don't have a buffer for the header, so we treat this as the header
                    // But standard markdown requires a separator row to be a table.
                    // A single line starting with | isn't necessarily a table.
                    // However, for this specific bot use case, assume yes.

                    closeParagraph();
                    closeList();

                    html += '<div class="table-container"><table><thead><tr>';
                    cells.forEach(cell => {
                        html += `<th>${parseInline(cell)}</th>`;
                    });
                    html += '</tr></thead><tbody>';
                }
            } else if (isSeparator) {
                // Store alignments
                state.tableAlignments = cells.map(cell => {
                    if (cell.startsWith(':') && cell.endsWith(':')) return 'center';
                    if (cell.endsWith(':')) return 'right';
                    return 'left';
                });
            } else {
                // Regular row
                closeParagraph(); // Should be closed but just in case
                closeList();

                html += '<tr>';
                cells.forEach((cell, idx) => {
                    const align = state.tableAlignments[idx] || 'left';
                    html += `<td style="text-align: ${align}">${parseInline(cell)}</td>`;
                });
                html += '</tr>';
            }
            continue;
        } else if (state.inTable) {
            // Not starting with pipe -> end table
            html += '</tbody></table></div>\n';
            state.inTable = false;
        }

        // --- 7. Empty Lines ---
        if (trimmed === '') {
            closeParagraph();
            closeList();
            closeTable();
            html += '<br>\n';
            continue;
        }

        // --- 8. Regular Text ---
        closeList();
        closeTable();

        if (!state.inParagraph) {
            html += '<p>';
            state.inParagraph = true;
            html += parseInline(line);
        } else {
            html += ' ' + parseInline(line);
        }
    }

    // Close any open tags
    closeParagraph();
    closeList();
    if (state.inCodeBlock) html += '</code></pre>\n';
    closeTable();

    return html;
}

// Helper to escape HTML
function escapeHtml(text) {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

// Helper to parse inline styles
function parseInline(text) {
    let html = escapeHtml(text);

    // Bold: **text** or __text__
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');

    // Italic: *text* or _text_
    html = html.replace(/\*([^\*]+)\*/g, '<em>$1</em>');
    html = html.replace(/\b_([^_]+)_\b/g, '<em>$1</em>');

    // Inline code: `code`
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Links: [text](url)
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

    return html;
}

/**
 * Apply markdown styles to message bubble
 */
function applyMarkdownStyles(bubble) {
    // Add styles for markdown elements
    const style = document.createElement('style');
    style.textContent = `
        .message-bubble h1,
        .message-bubble h2,
        .message-bubble h3 {
            margin: 16px 0 8px 0;
            font-weight: 700;
            line-height: 1.3;
            color: #f8fafc;
        }
        
        .message-bubble h1 { font-size: 1.6em; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 4px; }
        .message-bubble h2 { font-size: 1.4em; }
        .message-bubble h3 { font-size: 1.25em; color: #fbbf24; } /* Golden color for section headers */
        
        .message-bubble strong { font-weight: 800; color: #f1f5f9; }
        .message-bubble em { font-style: italic; }
        
        .message-bubble p {
            margin: 8px 0;
            line-height: 1.6;
        }
        
        .message-bubble code {
            background: rgba(0, 0, 0, 0.4);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Fira Code', 'Monaco', monospace;
            font-size: 0.9em;
            color: #fca5a5;
        }
        
        .message-bubble pre {
            background: #1e293b;
            padding: 16px;
            border-radius: 12px;
            overflow-x: auto;
            margin: 12px 0;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .message-bubble pre code {
            background: transparent;
            padding: 0;
            color: #e2e8f0;
            display: block;
        }
        
        .message-bubble a {
            color: #60a5fa;
            text-decoration: none;
            border-bottom: 1px dotted #60a5fa;
        }
        
        .message-bubble a:hover { color: #93c5fd; border-bottom-style: solid; }
        
        .message-bubble ul,
        .message-bubble ol {
            margin: 12px 0;
            padding-left: 28px;
        }
        
        .message-bubble li {
            margin: 6px 0;
            line-height: 1.6;
        }
        
        .message-bubble ul { list-style-type: disc; }
        .message-bubble ol { list-style-type: decimal; }
        
        .message-bubble blockquote {
            border-left: 4px solid #fbbf24;
            margin: 12px 0;
            padding: 4px 16px;
            background: rgba(251, 191, 36, 0.05);
            color: #cbd5e1;
            font-style: italic;
        }
        
        .message-bubble hr {
            border: 0;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            margin: 16px 0;
        }
        
        /* Table Styles */
        .message-bubble .table-container {
            overflow-x: auto;
            margin: 12px 0;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .message-bubble table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95em;
        }
        
        .message-bubble th {
            background: rgba(255, 255, 255, 0.1);
            padding: 10px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }
        
        .message-bubble td {
            padding: 8px 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .message-bubble tr:last-child td {
            border-bottom: none;
        }
        
        .message-bubble tr:hover td {
            background: rgba(255, 255, 255, 0.05);
        }
    `;

    if (!document.getElementById('markdown-styles')) {
        style.id = 'markdown-styles';
        document.head.appendChild(style);
    }
}

// Initialize markdown styles
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        applyMarkdownStyles();
    });
}

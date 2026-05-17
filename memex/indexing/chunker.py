from dataclasses import dataclass, field
from typing import Optional, Tuple, List
from pathlib import Path
from memex.core.config import config
import re
import uuid

'''This class will be used for every file in directory, separately. '''


@dataclass
class Chunk:
    '''Container for one chunk'''
    content: str
    source_file: str
    metadata: dict = field(default_factory=dict)
    id: str = field(default_factory= lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None
    parent_text: Optional[str] = None


class MarkdownChunker:
    '''Splits Markdown into chunks'''

    def __init__(self):
        self.chunk_size = config.indexing.chunk_size
        self.chunk_overlap = config.indexing.chunk_overlap
        self.use_parental = config.indexing.use_parental
    
    def process(self, file_path: Path) -> List[Chunk]:
        """Takes a file path and returns a list of chunks."""

        content = file_path.read_text(encoding='utf-8')
        source_file = str(file_path)

        section = self._split_by_headers(content)

        chunks = []
        for h1, h2, section_text in section:
            parent_chunk = Chunk(
                content=section_text,
                source_file=source_file,
                metadata={'h1':h1, 'h2': h2}
            )

            #check if the chunk length exceeded the limit
            if len(section_text) > self.chunk_size and self.use_parental:
                child_texts = self._split_by_size(section_text)
                
                # adding parent chunks
                chunks.append(parent_chunk)
                
                for i, child_text in enumerate(child_texts):
                    enriched = self._enrich(child_text, source_file, h1, h2)
                    chunks.append(Chunk(
                        content=enriched,
                        source_file=source_file,
                        metadata={"h1": h1, "h2": h2, "position": i},
                        parent_id=parent_chunk.id,
                        parent_text=section_text
                    ))

            else:
                parent_chunk.content = self._enrich(section_text, source_file, h1, h2)
                chunks.append(parent_chunk)
            
        return chunks


    def _split_by_headers(self, content: str) -> List[Tuple[str, str, str]]:
        '''
        Split markdown into headers
        
        Args:
            - content: markdown text
        
        Return:
            - list: (h1, h2, section text)
        '''
        
        #regular expression for headers search
        header_pattern = r'^(#{1,3})\s+(.+)$'
        sections = []
        
        current_h1 = ""
        current_h2 = ""
        current_content = []
        
        in_code_block = False  
        
        for line in content.split('\n'):

            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                current_content.append(line)
                continue
            
            if in_code_block:
                current_content.append(line)
                continue
            
            match = re.match(header_pattern, line)
            if match:
                if current_content:
                    sections.append((current_h1, current_h2, '\n'.join(current_content)))
                    current_content = []
                
                level = len(match.group(1))
                title = match.group(2).strip()
                
                if level == 1:
                    current_h1 = title
                    current_h2 = ""
                elif level == 2:
                    current_h2 = title
            else:
                current_content.append(line)
        
        if current_content:
            sections.append((current_h1, current_h2, '\n'.join(current_content)))
        
        return sections
    def _split_by_size(self, file_text: str) -> List[str]:
        '''
        Split a big chunk into smaller chunks with fixed size

        Args:
            - file_text

        Returns:
            - list of chunks 
        '''
        
        sentences = re.split(r'(?<=[.!?])\s+', file_text)
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if not current_chunk:
                potential_chunk = sentence
            else:
                potential_chunk = current_chunk + " " + sentence

            if len(potential_chunk) <= self.chunk_size:
                current_chunk = potential_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)

                if self.chunk_overlap > 0 and len(sentence) > self.chunk_overlap:
                    overlap_part = sentence[-self.chunk_overlap:]
                    current_chunk = overlap_part
                else:
                    current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _enrich(self, text: str, source: str, h1: str, h2: str) -> str:
        parts = [f"[File: {source}]"]
        if h1:
            parts.append(f"[{h1}]")
        if h2:
            parts.append(f"[{h2}]")
            if re.match(r'\d{2}-\d{2}-\d{4}', h2):
                try:
                    from datetime import datetime
                    dt = datetime.strptime(h2, "%d-%m-%Y")
                    # Несколько форматов для точного поиска
                    parts.append(f"[Date: {dt.strftime('%d %B %Y')}]")   # 18 April 2026
                    parts.append(f"[Date: {dt.strftime('%Y-%m-%d')}]")   # 2026-04-18
                    parts.append(f"[Date: {dt.strftime('%d.%m.%Y')}]")   # 18.04.2026
                except ValueError:
                    pass
        parts.append(text)
        return "\n".join(parts)



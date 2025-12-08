#!/usr/bin/env python3
"""
Pentaho Parser - Extract metadata from Pentaho XML files (.ktr/.kjb)

This script parses Pentaho transformation and job files to extract structured
metadata for migration to DBT on Snowflake.
"""

import xml.etree.ElementTree as ET
import json
import re
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set


class PentahoParser:
    """Parser for Pentaho XML files (.ktr transformations and .kjb jobs)"""

    # Regex pattern to find variables like ${VARIABLE_NAME}
    VARIABLE_PATTERN = re.compile(r'\$\{([A-Z_0-9]+)\}')

    def __init__(self, directory_path: str, registry_path: Optional[str] = None):
        """
        Initialize parser with directory path

        Args:
            directory_path: Path to directory containing Pentaho files
            registry_path: Path to migration_registry.json (auto-detected if None)
        """
        self.directory_path = Path(directory_path)

        # Determine output path: if input is pentaho-sources/, output to dimensions/
        input_path_str = str(self.directory_path)
        if "queries" in input_path_str:
            # Replace pentaho-sources/ with dimensions/ for output
            output_path_str = input_path_str.replace("queries", "dimensions")
            self.output_path = Path(output_path_str) / "metadata" / "pentaho_raw.json"
        else:
            # Default: output to same directory
            self.output_path = self.directory_path / "metadata" / "pentaho_raw.json"

        self.files_metadata = []

        # Find registry path - look for config/migration_registry.json in project root
        if registry_path:
            self.registry_path = Path(registry_path)
        else:
            # Auto-detect: go up from directory_path to find config/migration_registry.json
            current = self.directory_path.resolve()
            while current.parent != current:
                registry_candidate = current / "config" / "migration_registry.json"
                if registry_candidate.exists():
                    self.registry_path = registry_candidate
                    break
                current = current.parent
            else:
                self.registry_path = None

        self.registry_data = self._load_registry()
        self.already_parsed_files: Set[str] = set()

    def _load_registry(self) -> Dict[str, Any]:
        """Load the migration registry"""
        if not self.registry_path or not self.registry_path.exists():
            return {
                "version": "1.0",
                "last_updated": None,
                "parsed_files": {},
                "migrated_tables": {},
                "statistics": {
                    "total_dimensions": 0,
                    "total_pentaho_files": 0,
                    "total_tables": 0,
                    "completed_migrations": 0,
                    "pending_migrations": 0
                }
            }

        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print(f"[WARNING] Could not read registry at {self.registry_path}", file=sys.stderr)
            return {"parsed_files": {}}

    def _save_registry(self) -> None:
        """Save the updated migration registry"""
        if not self.registry_path:
            return

        self.registry_data["last_updated"] = datetime.now().isoformat()

        try:
            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump(self.registry_data, f, indent=2, ensure_ascii=False)
            print(f"[OK] Registry updated: {self.registry_path}")
        except IOError as e:
            print(f"[WARNING] Could not save registry: {e}", file=sys.stderr)

    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of a file"""
        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

    def _is_file_already_parsed(self, file_path: Path) -> bool:
        """Check if file has already been parsed"""
        file_name = file_path.name

        if file_name not in self.registry_data.get("parsed_files", {}):
            return False

        # Check if hash matches (file hasn't changed)
        stored_hash = self.registry_data["parsed_files"][file_name].get("hash")
        current_hash = self._get_file_hash(file_path)

        return stored_hash == current_hash

    def _register_parsed_file(self, file_path: Path, dimension: str) -> None:
        """Register a file as parsed in the registry"""
        file_name = file_path.name
        file_hash = self._get_file_hash(file_path)

        if "parsed_files" not in self.registry_data:
            self.registry_data["parsed_files"] = {}

        self.registry_data["parsed_files"][file_name] = {
            "hash": file_hash,
            "parsed_at": datetime.now().isoformat(),
            "dimension": dimension,
            "file_path": str(file_path)
        }

        self.already_parsed_files.add(file_name)

    def parse_all_files(self) -> Dict[str, Any]:
        """
        Parse all .ktr and .kjb files in the directory

        Returns:
            Dictionary with parsed metadata
        """
        if not self.directory_path.exists():
            print(f"Error: Directory {self.directory_path} does not exist", file=sys.stderr)
            return {"files": []}

        # Find all Pentaho files
        ktr_files = list(self.directory_path.glob("*.ktr"))
        kjb_files = list(self.directory_path.glob("*.kjb"))

        print(f"Found {len(ktr_files)} transformation(s) and {len(kjb_files)} job(s)")

        # Detect dimension name from path
        # If path is dimensions/dim_X/ then parent is dimensions, so use the directory name itself
        path_name = self.directory_path.name
        dimension_name = path_name if path_name.startswith('dim_') else "unknown"

        # Track statistics
        skipped_count = 0
        parsed_count = 0

        # Parse transformations
        for ktr_file in ktr_files:
            # Check if already parsed
            if self._is_file_already_parsed(ktr_file):
                print(f"[SKIP] Already parsed: {ktr_file.name}")
                self.already_parsed_files.add(ktr_file.name)
                skipped_count += 1
                continue

            try:
                metadata = self.parse_transformation(ktr_file)
                if metadata:
                    self.files_metadata.append(metadata)
                    self._register_parsed_file(ktr_file, dimension_name)
                    parsed_count += 1
                    print(f"[OK] Parsed transformation: {ktr_file.name}")
            except Exception as e:
                print(f"[ERROR] Error parsing {ktr_file.name}: {str(e)}", file=sys.stderr)

        # Parse jobs
        for kjb_file in kjb_files:
            # Check if already parsed
            if self._is_file_already_parsed(kjb_file):
                print(f"[SKIP] Already parsed: {kjb_file.name}")
                self.already_parsed_files.add(kjb_file.name)
                skipped_count += 1
                continue

            try:
                metadata = self.parse_job(kjb_file)
                if metadata:
                    self.files_metadata.append(metadata)
                    self._register_parsed_file(kjb_file, dimension_name)
                    parsed_count += 1
                    print(f"[OK] Parsed job: {kjb_file.name}")
            except Exception as e:
                print(f"[ERROR] Error parsing {kjb_file.name}: {str(e)}", file=sys.stderr)

        # Update statistics
        if "statistics" in self.registry_data:
            self.registry_data["statistics"]["total_pentaho_files"] = len(self.registry_data.get("parsed_files", {}))

        print(f"\nSummary: {parsed_count} newly parsed, {skipped_count} skipped (already in registry)")

        return {"files": self.files_metadata}

    def parse_transformation(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse a .ktr transformation file

        Args:
            file_path: Path to .ktr file

        Returns:
            Dictionary with transformation metadata
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except ET.ParseError as e:
            print(f"XML Parse Error in {file_path.name}: {str(e)}", file=sys.stderr)
            return None

        # Extract basic info
        trans_name = self._get_text(root, 'info/name', file_path.stem)
        trans_description = self._get_text(root, 'info/description', '')

        # Detect level from filename
        level = self._detect_level(file_path.name)

        # Parse steps
        steps = []
        sql_queries = []
        tables_input = []
        tables_output = []
        variables = set()

        for step in root.findall('.//step'):
            step_data = self._parse_step(step)
            if step_data:
                steps.append(step_data)

                # Collect SQL queries
                if step_data.get('sql_query'):
                    sql_queries.append(step_data['sql_query'])

                # Collect table references
                if step_data.get('table_name'):
                    if step_data['step_type'] in ['TableInput', 'DBLookup', 'DatabaseJoin']:
                        tables_input.append(step_data['table_name'])
                    elif step_data['step_type'] in ['TableOutput', 'InsertUpdate', 'Update', 'VerticaBulkLoader', 'ExcelOutput', 'TextFileOutput']:
                        tables_output.append(step_data['table_name'])

        # Extract variables from all text content
        all_text = ET.tostring(root, encoding='unicode', method='text')
        variables.update(self.VARIABLE_PATTERN.findall(all_text))

        # Calculate statistics
        sql_steps = len([s for s in steps if s.get('sql_query')])
        complexity = self._estimate_complexity(len(steps))

        return {
            "file_name": file_path.name,
            "file_type": "transformation",
            "level": level,
            "transformation_name": trans_name,
            "description": trans_description,
            "variables": sorted(list(variables)),
            "sql_queries": sql_queries,
            "tables_input": list(set(tables_input)),
            "tables_output": list(set(tables_output)),
            "steps": steps,
            "statistics": {
                "total_steps": len(steps),
                "sql_steps": sql_steps,
                "estimated_complexity": complexity
            }
        }

    def parse_job(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse a .kjb job file

        Args:
            file_path: Path to .kjb file

        Returns:
            Dictionary with job metadata
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except ET.ParseError as e:
            print(f"XML Parse Error in {file_path.name}: {str(e)}", file=sys.stderr)
            return None

        # Extract basic info
        job_name = self._get_text(root, 'name', file_path.stem)
        job_description = self._get_text(root, 'description', '')

        # Parse entries
        entries = []
        transformations_called = []
        variables = set()

        for entry in root.findall('.//entry'):
            entry_data = self._parse_job_entry(entry)
            if entry_data:
                entries.append(entry_data)

                # Track transformation calls
                if entry_data.get('type') == 'TRANS' and entry_data.get('filename'):
                    transformations_called.append(entry_data['filename'])

        # Extract variables
        all_text = ET.tostring(root, encoding='unicode', method='text')
        variables.update(self.VARIABLE_PATTERN.findall(all_text))

        # Detect level
        level = self._detect_level(file_path.name)

        return {
            "file_name": file_path.name,
            "file_type": "job",
            "level": level,
            "job_name": job_name,
            "description": job_description,
            "variables": sorted(list(variables)),
            "transformations_called": transformations_called,
            "entries": entries,
            "statistics": {
                "total_entries": len(entries),
                "transformation_calls": len(transformations_called),
                "estimated_complexity": self._estimate_complexity(len(entries))
            }
        }

    def _parse_step(self, step_element: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse a transformation step"""
        step_name = self._get_text(step_element, 'name', 'Unknown')
        step_type = self._get_text(step_element, 'type', 'Unknown')

        step_data = {
            "step_name": step_name,
            "step_type": step_type
        }

        # Extract connection name
        connection = self._get_text(step_element, 'connection', None)
        if connection:
            step_data['connection'] = connection

        # Extract SQL query (handle CDATA)
        sql_query = self._get_text(step_element, 'sql', None)
        if sql_query:
            step_data['sql_query'] = sql_query.strip()

        # Extract table name
        table_name = self._get_text(step_element, 'table', None)
        if not table_name:
            # Try schema + table combination
            schema = self._get_text(step_element, 'schema', None)
            table = self._get_text(step_element, 'table', None)
            if schema and table:
                table_name = f"{schema}.{table}"
            elif table:
                table_name = table

        if table_name:
            step_data['table_name'] = table_name

        # === NEW: Extract database operation metadata ===
        # For TableOutput steps
        if step_type == 'TableOutput':
            # Extract truncate flag
            truncate = self._get_text(step_element, 'truncate', None)
            if truncate:
                step_data['truncate'] = truncate.upper() == 'Y'

            # Extract commit size
            commit_size = self._get_text(step_element, 'commit', None)
            if commit_size:
                step_data['commit_size'] = commit_size

        # For InsertUpdate steps
        elif step_type == 'InsertUpdate':
            # Extract update/insert mode
            update_bypassed = self._get_text(step_element, 'update_bypassed', None)
            step_data['is_merge'] = True
            if update_bypassed:
                step_data['update_bypassed'] = update_bypassed.upper() == 'Y'

            # Extract key fields
            key_lookup = step_element.find('lookup')
            if key_lookup is not None:
                key_fields = []
                for key_field in key_lookup.findall('key'):
                    key_name = self._get_text(key_field, 'name', None)
                    if key_name:
                        key_fields.append(key_name)
                if key_fields:
                    step_data['key_fields'] = key_fields

        # For Update steps
        elif step_type == 'Update':
            step_data['is_update'] = True
            # Extract key fields
            key_lookup = step_element.find('lookup')
            if key_lookup is not None:
                key_fields = []
                for key_field in key_lookup.findall('key'):
                    key_name = self._get_text(key_field, 'name', None)
                    if key_name:
                        key_fields.append(key_name)
                if key_fields:
                    step_data['key_fields'] = key_fields

        # For Delete steps
        elif step_type == 'Delete':
            step_data['is_delete'] = True

        # === END NEW ===

        # Extract lookup/join details if applicable
        if step_type in ['DBLookup', 'DatabaseJoin']:
            lookup_table = self._get_text(step_element, 'lookup/table', None)
            if lookup_table:
                step_data['lookup_table'] = lookup_table

        return step_data

    def _parse_job_entry(self, entry_element: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse a job entry"""
        entry_name = self._get_text(entry_element, 'name', 'Unknown')
        entry_type = self._get_text(entry_element, 'type', 'Unknown')

        entry_data = {
            "entry_name": entry_name,
            "type": entry_type
        }

        # Extract filename for transformation entries
        if entry_type == 'TRANS':
            filename = self._get_text(entry_element, 'filename', None)
            if filename:
                entry_data['filename'] = filename

        # Extract SQL for SQL entries
        if entry_type == 'SQL':
            sql = self._get_text(entry_element, 'sql', None)
            if sql:
                entry_data['sql'] = sql.strip()

            connection = self._get_text(entry_element, 'connection', None)
            if connection:
                entry_data['connection'] = connection

        return entry_data

    def _get_text(self, element: ET.Element, path: str, default: Any = None) -> Any:
        """
        Safely get text from XML element by path

        Args:
            element: XML element to search in
            path: XPath-like path (supports simple paths with /)
            default: Default value if not found

        Returns:
            Text content or default
        """
        try:
            found = element.find(path)
            if found is not None and found.text:
                return found.text.strip()
            return default
        except Exception:
            return default

    def _detect_level(self, filename: str) -> Optional[str]:
        """
        Detect layer level from filename prefix

        Args:
            filename: Name of the file

        Returns:
            Level identifier or None
        """
        filename_lower = filename.lower()

        if filename_lower.startswith('adq_'):
            return 'adq'
        elif filename_lower.startswith('mas_'):
            return 'mas'
        elif filename_lower.startswith('d_'):
            return 'dimension'
        elif filename_lower.startswith('f_'):
            return 'fact'

        return None

    def _estimate_complexity(self, step_count: int) -> str:
        """
        Estimate complexity based on step/entry count

        Args:
            step_count: Number of steps or entries

        Returns:
            Complexity level: low, medium, or high
        """
        if step_count < 5:
            return 'low'
        elif step_count <= 15:
            return 'medium'
        else:
            return 'high'

    def write_output(self, data: Dict[str, Any]) -> None:
        """
        Write parsed metadata to JSON file and update registry

        Args:
            data: Metadata dictionary to write
        """
        # Create metadata directory if it doesn't exist
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write JSON with nice formatting
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\n[SUCCESS] Metadata written to: {self.output_path}")
        print(f"  Total files processed: {len(data['files'])}")

        # Save registry
        self._save_registry()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Parse Pentaho XML files and extract metadata for DBT migration'
    )
    parser.add_argument(
        'directory',
        help='Directory containing Pentaho .ktr and .kjb files'
    )
    parser.add_argument(
        '--output',
        help='Custom output path (default: <directory>/../metadata/pentaho_raw.json)',
        default=None
    )

    args = parser.parse_args()

    # Initialize parser
    pentaho_parser = PentahoParser(args.directory)

    # Override output path if specified
    if args.output:
        pentaho_parser.output_path = Path(args.output)

    # Parse all files
    print(f"Parsing Pentaho files in: {pentaho_parser.directory_path}")
    print("-" * 60)

    metadata = pentaho_parser.parse_all_files()

    # Write output
    if metadata['files']:
        pentaho_parser.write_output(metadata)
    else:
        # Check if files were skipped (already in registry)
        if len(pentaho_parser.already_parsed_files) > 0:
            print("\n[OK] All files already parsed and in registry. No new files to process.")
            # Still save registry in case statistics changed
            pentaho_parser._save_registry()
            sys.exit(0)
        else:
            print("\n[WARNING] No files were successfully parsed", file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()

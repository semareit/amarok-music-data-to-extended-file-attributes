#!/usr/bin/env python3
"""
Script to extract Amarok music data from MySQL and create a metadata.txt file
in the correct format for setfattr --restore
"""

import mysql.connector
import os
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AmarokXattrExporter:
    def __init__(self, db_host='localhost', db_port=3306, db_user='amarok', db_password='amarok', db_name='amarok'):
        self.db_config = {
            'host': db_host,
            'port': db_port,
            'user': db_user,
            'password': db_password,
            'database': db_name
        }
    
    def connect_to_database(self):
        """Connect to MySQL database"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            logger.info(f"Successfully connected to Amarok database ({self.db_config['host']}:{self.db_config['port']})")
            return conn
        except mysql.connector.Error as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    def get_music_data(self):
        """
        Extract music data from Amarok database
        Returns generator with filepath, labels and rating
        """
        conn = self.connect_to_database()
        if not conn:
            return
        
        cursor = conn.cursor(dictionary=True)
        
        # SQL query based on database schema with correct path construction
        query = """
        SELECT 
            CONCAT(d.lastmountpoint, '/', TRIM(LEADING '.' FROM u.rpath)) as filepath,
            l.label as label,
            s.rating as rating
        FROM urls u
        LEFT JOIN statistics s ON u.id = s.url
        LEFT JOIN urls_labels ul ON u.id = ul.url
        LEFT JOIN labels l ON ul.label = l.id
        LEFT JOIN devices d ON u.deviceid = d.id
        WHERE u.rpath IS NOT NULL 
          AND u.rpath != ''
          AND d.lastmountpoint IS NOT NULL
        ORDER BY u.id, l.label
        """
        
        try:
            cursor.execute(query)
            
            # Group data by filepath (since one file can have multiple labels)
            file_data = {}
            for row in cursor:
                filepath = row['filepath']
                
                if not filepath:
                    continue
                
                # Normalize path (remove double slashes, etc.)
                filepath = os.path.normpath(filepath)
                
                if filepath not in file_data:
                    file_data[filepath] = {
                        'labels': set(),
                        'rating': row['rating']
                    }
                
                # Add label if present
                if row['label']:
                    file_data[filepath]['labels'].add(row['label'])
            
            # Convert sets to strings
            for filepath, data in file_data.items():
                data['labels_str'] = ','.join(sorted(data['labels'])) if data['labels'] else ''
                yield filepath, data
                
        except mysql.connector.Error as e:
            logger.error(f"Error querying data: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def convert_rating(self, amarok_rating):
        """
        Convert Amarok rating (0-10) to Baloo rating (0-10)
        """
        if amarok_rating is None:
            return "0"
        
        # Amarok: 0-10, Baloo: 0-10 (same scale)
        return str(int(amarok_rating))
    
    def generate_restore_file(self, output_file='metadata.txt'):
        """
        Generate a metadata.txt file in the correct format for setfattr --restore
        """
        file_count = 0
        processed_count = 0
        attribute_count = 0
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for filepath, data in self.get_music_data():
                file_count += 1
                
                # Check if file exists
                if not os.path.exists(filepath):
                    logger.warning(f"File not found: {filepath}")
                    continue
                
                processed_count += 1
                
                # Write file comment
                f.write(f"# file: {filepath}\n")
                
                # Write rating attribute
                rating = self.convert_rating(data['rating'])
                f.write(f'user.baloo.rating="{rating}"\n')
                attribute_count += 1
                
                # Write labels attribute if present
                if data['labels_str']:
                    f.write(f'user.xdg.tags="{data["labels_str"]}"\n')
                    attribute_count += 1
                
                # Empty line between files
                f.write("\n")
                
                logger.info(f"Entries for: {os.path.basename(filepath)}")
                logger.debug(f"  Rating: {data['rating']} -> {rating}")
                logger.debug(f"  Labels: {data['labels_str']}")
        
        logger.info(f"metadata.txt created: {output_file}")
        logger.info(f"Processed: {processed_count} of {file_count} files")
        logger.info(f"Total attributes: {attribute_count}")
        
        return processed_count, attribute_count

def main():
    parser = argparse.ArgumentParser(description='Generate metadata.txt for setfattr --restore from Amarok data')
    parser.add_argument('--host', default='localhost', help='MySQL Host (default: localhost)')
    parser.add_argument('--port', default=3306, type=int, help='MySQL Port (default: 3306)')
    parser.add_argument('--user', default='amarok', help='MySQL User (default: amarok)')
    parser.add_argument('--password', default='amarok', help='MySQL Password (default: amarok)')
    parser.add_argument('--database', default='amarok', help='MySQL Database (default: amarok)')
    parser.add_argument('--output', '-o', default='metadata.txt', help='Output file (default: metadata.txt)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize exporter
    exporter = AmarokXattrExporter(
        db_host=args.host,
        db_port=args.port,
        db_user=args.user,
        db_password=args.password,
        db_name=args.database
    )
    
    # Generate restore file
    file_count, attr_count = exporter.generate_restore_file(output_file=args.output)
    
    print(f"\nSummary:")
    print(f"Created file: {args.output}")
    print(f"Processed files: {file_count}")
    print(f"Total attributes: {attr_count}")
    print(f"\nUsage:")
    print(f"setfattr -h --restore={args.output}")

if __name__ == "__main__":
    main()
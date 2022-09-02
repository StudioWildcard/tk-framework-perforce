from re import template
import yaml
import sys
import os
import logging

from .schema_resolver import Transformers



class Schema(object):
    
    def __init__(self, schema_type=None, template_schema=None):


        self.schema = None
        self.type = schema_type
        
        if template_schema != None:
            schema = self.load_schema_from_yaml(template_schema)
            self.schema = schema

        
    def load_schema_from_yaml(self, name_of_file):
        #TODO consider if the yaml file does not exist in the same folder.
        
        file_name = name_of_file + ".yml"
        dir_path = sys.path[0]
        path = dir_path + "\\" + file_name

        try:
            with open(path) as f:
                schema = yaml.safe_load(f)
            
                # set the type attribute so we know which template we are using
                self.type = list(schema.keys())[0]
                return schema
            
        except FileNotFoundError:
            files = os.listdir(sys.path[0])
            files.remove('schema.py')
            logging.error('Schema template not valid, the following template files are available:')
            print(files)
                     
    


    @property
    def schema_type(self):
        return self.type  
    
    @property
    def print_schema(self):
        #TODO remove this. just for testing
        print(self.schema)
    

    #example: Schema.from_name("asset_item")
    #TODO lets ensure we have an empty class that can run get instatiated via class method
    @classmethod
    def from_schema_name(cls, name):
        cls.setup_as("asset_item")

        return cls

    @classmethod
    def set_schema_type(cls, type):
        
        """
        Description: change the schema type after class is created

        type: [str] type for the schema. For example Sync_item.
        """
        
        cls.type = type
        
        
    
    
    def validate_schema(self):
        
        validation_keys = ['key', 'title', 'Name']

        if self.schema.get('key') is None:
            raise KeyError('Schema not valid, value for key not found')
        else:
            print('validation passed')    
                    
                    
    def create_schema(self, type=None, key=None, title=None, delegate=None):
        
        #self.type = type if type != None else "custom"
        
        schema = {'default': 'No name'}
        
        schema['key'] = key
        schema['title'] = title
        schema['deletage'] = delegate
        
        #need to validate schema after creation. Should it happen here or should that be a specific call afterwards?
        self.schema = schema
        self.validate_schema()
        
        
        
        
a = Schema(template_schema='asset_item')
print(a.type)
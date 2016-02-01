from collections import OrderedDict
import json
import xmltodict
from copy import deepcopy

class DataModelDict(OrderedDict):
    """Class for handling json/xml equivalent data structures."""
    
    def __init__(self, *args, **kwargs):
        """
        Initilizes a DataModelDict. Can be initilized like an OrderedDict, or by supplying a json/xml string or file-like object.
        
        Additional Keyword Arguments when initilizing with json/xml info:
        parse_float -- data type to use for floating point values parsed from the json/xml info
        parse_int -- data type to use for integer values parsed from the json/xml info
        """
       
        OrderedDict.__init__(self)
        if len(args) == 1:
            try:
                parse_float = kwargs.get('parse_float', None)
                parse_int = kwargs.get('parse_int', None)
                self.load(args[0], parse_float=parse_float, parse_int=parse_int)
            except:
                self.update(*args, **kwargs)
        else:
            self.update(*args, **kwargs)
   
    def append(self, key, value):
        """If key not assigned, assigns key. If key assigned, appends value to the current value (and converts to list if needed)."""
        if key in self:
            if isinstance(self[key], list):
                self[key].append(value)
            else:
                self[key] = [self[key]]
                self[key].append(value)
        else:
            self[key] = value

    def find(self, key, **kwargs):
        """
        Return a DataModelDict corresponding to a subelement given by key. Additional keyword arguments can be used to refine the search.
        
        Arguments:
        key -- key name for the subelement
        Any additional keyword arguments refine the search by ensuring that the subelement contains the correct key-value pairs.
        
        If no matching subelements are found, returns None.
        If exactly one matching subelement is found, returns DataModelDict with key - subelement.
        If multiple matching subelements, issues an error.
        """
        matching = []
        for subelement in self.iterfindall(key):
            match = True
            for skey, svalue in kwargs.iteritems():
                for test in subelement.iterfindall(skey):
                    if test != svalue:
                        match = False
                        break
                if not match:
                    break
            if match:
                matching.append(subelement)
                
        if len(matching) == 0:
            return None
        elif len(matching) == 1:
            return DataModelDict([(key, matching[0])])
        else:
            raise ValueError('Unique subelement not identified.')            

    def findall(self, key):
        """Return a list of all subelements at any level with the given key name."""
        return [val for val in self.iterfindall(key)]     
            
    def iterfindall(self, key):
        """Return an iterator over all recursive elements with a given key"""
        return self.__gen_dict_extract(key, self)
    
    def iterlist(self, key):
        """Return an iterator over an element's value(s).  Useful if the element may or may not be a list of values."""
        if isinstance(self[key], list):
            for val in self[key]:
                yield val
        else:
            yield self[key]        
    
    def list(self, key):
        """Return an element's value(s) as a list.  Useful if the element may or may not be a list of values."""
        return [val for val in self.iterlist(key)]
    
    def load(self, model, parse_float=None, parse_int=None):
        """
        Read in values from a json/xml string or file-like object.
        
        Keyword Arguments:
        parse_float -- data type to use for floating point values parsed from the json/xml info
        parse_int -- data type to use for integer values parsed from the json/xml info
        """
        
        #load from string
        if isinstance(model, (str, unicode)):
            
            #try json interpreter
            try:
                self.update(json.loads(model, object_pairs_hook=DataModelDict, parse_int=parse_int, parse_float=parse_float))
            except:
                
                #try xml interpreter
                if True:
                    if parse_float is None:
                        parse_float = float
                    if parse_int is None:
                        parse_int = int
                    hold = xmltodict.parse(model)
                    self.update(self.__xml_val_parse(hold, parse_int, parse_float))
                else:
                    raise ValueError('String is not acceptable json or xml')
        
        #load from file
        elif hasattr(model, 'read'):
            #try json interpreter
            try:
                self.update(json.load(model, object_pairs_hook=DataModelDict, parse_int=parse_int, parse_float=parse_float))
            except:
                model.seek(0)
                #try xml interpreter
                if True:
                    if parse_float is None:
                        parse_float = float
                    if parse_int is None:
                        parse_int = int
                    hold = xmltodict.parse(model)
                    self.update(self.__xml_val_parse(hold, parse_int, parse_float))
                else:
                    raise ValueError('File is not acceptable json or xml')
        else:
            raise TypeError('Can only load json/xml strings or file-like objects')
    
    def json(self, fp=None, indent=None, separators=(', ', ': ')):
        """
        Return the DataModelDict in json format.
        
        Keyword Arguments:
        fp -- file-like object.  If given, the json will be written to fp instead of returned as a string.
        indent -- int number of spaces to indent lines.  If not given, the output will be inline.
        separators --  an (item_separator, dict_separator) tuple. Default is (', ', ': ').
        """
        
        if fp is None:
            return json.dumps( self, indent=indent, separators=separators)
        else:
            json.dump(self, fp, indent=indent, separators=separators)
    
    def xml(self, fp=None, indent=None, full_document=True):
        """
        Return the DataModelDict in xml format.
        
        Keyword Arguments:
        fp -- file-like object.  If given, the xml will be written to fp instead of returned as a string.
        indent -- int number of spaces to indent lines.  If not given, the output will be inline.
        full_document -- boolean indicating if the output is associated with a full xml model.  If True, it must have only one maximum element, and a header is added.
        """
        if indent is None:
            indent = ''
            newl = ''
        else:
            indent = ''.join([' ' for i in xrange(indent)])
            newl = '\n'

        return xmltodict.unparse(self, output=fp, pretty=True, indent=indent, newl=newl, full_document=full_document)    
    
    def __xml_val_parse(self, var, parse_int, parse_float):
        """Internal method for parsing xml for converting meaningful strings to values."""
        if hasattr(var, 'iteritems'):
            for k, v in var.iteritems():
                var[k] = self.__xml_val_parse(v, parse_int, parse_float)
            return DataModelDict(var)
        elif hasattr(var, '__iter__'):
            for i in xrange(len(var)):
                var[i] = self.__xml_val_parse(var[i], parse_int, parse_float)
            return var
        elif isinstance(var, (str, unicode)):   
            if var == '':
                return None
            elif var == 'True' or var == 'true':
                return True
            elif var == 'False' or var == 'false':
                return False
            elif var == '-Infinity' or var == '-Inf' or var == '-inf':
                return float('-Inf')            
            elif var == 'Infinity' or var == 'Inf' or var == 'inf':
                return float('Inf')            
            elif var == 'NaN' or var == 'nan':
                return float('NaN')
            else:
                try:
                    return parse_int(var)
                except:
                    try:
                        return parse_float(var)
                    except:
                        return var
        else:
            return var
                   
    def __gen_dict_extract(self, key, var):    
        if hasattr(var,'iteritems'):
            for k, v in var.iteritems():
                if k == key:
                    if isinstance(v, list):
                        for d in v:
                            yield d
                    else:
                        yield v
                if isinstance(v, dict):
                    for result in self.__gen_dict_extract(key, v):
                        yield result
                elif isinstance(v, list):
                    for d in v:
                        for result in self.__gen_dict_extract(key, d):
                            yield result                      
    
    def key_to_html(self, key):
        """Return a new DataModelDict where all recursive elements with a given key are converted to strings (useful when html included in xml)."""
        return self.__gen_html(key, deepcopy(self))
    
    def __gen_html(self, key, var):
        if hasattr(var,'iteritems'):
            for k, v in var.iteritems():
                if k == key:
                    if isinstance(v, dict):
                        var[k] = v.xml(full_document=False)
                    elif isinstance(v, list):
                        for d in xrange(len(v)):
                            var[k][d] = v[d].xml(full_document=False)
                        var[k] = ''.join(var[k])
                else:
                    if isinstance(v, dict):
                        var[k] = self.__gen_html(key, v)
                    elif isinstance(v, list):
                        for d in xrange(len(v)):
                            var[k][d] = self.__gen_html(key, v[d])
        return var    
        
    
    
    
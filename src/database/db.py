#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 21 juin 2010. Copyright 2010, David GUEZ
@author: david guez (guezdav@gmail.com)
This file is a part of the source code of the MALODOS project.
You can use and distribute it freely, but have to conform to the license
attached to this project (LICENSE.txt file)
=====================================================================

interface between the application and the database engine
'''

import sqlite3
import datetime
import hashlib
import string
import gui.utilities
import os.path
import ConfigParser
import algorithms.words
import Resources

class ConfigReader(object):
    def __init__(self,conf_file=None):
        self.config = None
        self.conf_file = conf_file
        if conf_file is None : return
        if not os.path.exists(self.conf_file) :
            try:
                theFile = open(self.conf_file,'w')
            except:
                return
            theFile.close()
        self.config = ConfigParser.SafeConfigParser()
        self.read_config()

    def get_param(self,section,key,defaultValue=None,create_if_not_exist=False):
        #if not self.config : raise _("Configuration not found")
        try:
            return self.config.get(section,key)
        except Exception as E:
            if defaultValue is None : raise E
            if create_if_not_exist :
                try:
                    self.set_param(section,key,defaultValue,True)
                except Exception as Ex:
                    raise Ex
            return defaultValue
                
    def set_param(self,section,key,value,allow_create_section=True):
        if not self.config : raise _("Configuration not found")
        if not self.config.has_section(section) and allow_create_section: self.config.add_section(section)
        return self.config.set(section, key,value)
    def get_all_params_in(self,section):
        if not self.config : raise _("Configuration not found")
        if not self.config.has_section(section) : return dict()
        return dict(self.config.items(section))
    def read_config(self):
        if os.path.exists(self.conf_file) :
            self.config = ConfigParser.SafeConfigParser()
            self.config.read(self.conf_file)
    def commit_config(self):
            try:
                theFile = open(self.conf_file,'w')
                self.config.write(theFile)
                theFile.close()
                return True
            except:
                return False

class OCRConfiguration(ConfigReader):
    def __init__(self,conf_file):
        ConfigReader.__init__(self,conf_file)
    def get_available_ocr_programs(self):
        return self.config.sections()
    def get_needed_image_format(self,ocr_sequence):
        return self.get_param(ocr_sequence, 'inputFormat', 'tif', False)
    def get_output_format(self,ocr_sequence):
        return self.get_param(ocr_sequence, 'outputFormat', 'ascii', False).lower()
    def build_call_sequence(self,ocr_section,input_file,output_file):
        needed_format = self.get_needed_image_format(ocr_section).lower()
        if os.path.splitext(input_file)[1].lower() != '.'+  needed_format :
            msg = _('Unable to get the image in format %(needed_format) for section %(section) ') % {'needed_format':needed_format,'ocr_section':ocr_section}
            gui.utilities.show_message(msg)
            return []
        pname = self.get_param(ocr_section, 'programName', '', False)
        if pname == '' : return []
        placeHolder = ['','','']
        to_place=[]
        try:
            to_place.append(self.get_param(ocr_section, 'inputOption', None, False))
            to_place.append(self.get_param(ocr_section, 'outputOption', None, False))
            otherOpts = self.get_param(ocr_section, 'otherOptions', '', False)
            if otherOpts != '' : to_place.append(otherOpts)
        except:
            return []
        to_place2=[]
        outF=None
        for s in to_place:
            if s.startswith('$1') or s.startswith('$2') or s.startswith('$3'):
                ps = int(s[1])-1
                s=s[2:]
                if placeHolder[ps] != '':
                    msg = _('Misformatted OCR configuration for section %s ')% ocr_section
                    gui.utilities.show_message(msg) 
                    return ([],None)
                else:
                    placeHolder[ps] = s
            elif s.startswith('>'):
                outF = s[1:]
            else:
                to_place2.append(s)
        for s in to_place2:
            no_placed=True
            for i in range(len(placeHolder)) :
                if placeHolder[i] == '' :
                    placeHolder[i] = s
                    not_placed=False
                    break
            if not_placed :
                msg = _('Misformatted OCR configuration for section %s ')% ocr_section
                gui.utilities.show_message(msg) 
                return ([],None)
        def do_replace(s):
            s = s.replace("$outputFilenameNoExt" , os.path.splitext(output_file)[0])
            s = s.replace("$outputFilename" , output_file)
            s = s.replace("$inputFilenameNoExt" , os.path.splitext(input_file)[0])
            s = s.replace("$inputFilename" , input_file)
            return s
            
        for i in range(len(placeHolder)) :
            placeHolder[i] = do_replace(placeHolder[i])
        if outF is not None : outF=do_replace(outF)
        ans = [pname]
        for s in placeHolder : ans.extend(s.split())
        return (ans,outF)


class Configuration(ConfigReader):
    def __init__(self):
        if os.name=='nt':
            self.conf_dir = os.path.join(os.path.expanduser('~'),'malodos')
        else:
            self.conf_dir = os.path.join(os.path.expanduser('~'),'.malodos')
        if not os.path.isdir(self.conf_dir) :
            try:
                os.mkdir(self.conf_dir)
            except:
                ConfigReader.__init__(self)
                return
        if not os.path.exists(self.conf_dir) :
            ConfigReader.__init__(self)
            return
        conf_file = os.path.join(self.conf_dir,'malodos.ini')
        fillConf = not os.path.exists(conf_file) 
        ConfigReader.__init__(self,conf_file)
        if  fillConf and os.path.exists(self.conf_file) and self.config is not None:
            self.config.add_section('database')
            self.set_database_name( os.path.join(self.conf_dir,'malodos.db'))
            self.config.add_section('scanner')
            self.set_current_scanner('None')
            self.config.add_section('language')
            self.set_installed_languages(u'english')
            self.set_current_language('english')
            self.config.add_section('survey')
            self.set_survey_directory_list( (os.path.join(self.conf_dir,'documents'),) , (0,))
            self.set_survey_extension_list( 'png tif tiff pdf jpg jpeg gif bmp' )
            self.commit_config()
        self.read_config()

    def get_survey_extension_list(self):
        return self.get_param('survey', 'extension_list')
    def set_survey_extension_list(self,S):
        return self.set_param('survey', 'extension_list',S)
    def get_survey_directory_list(self):
        S = self.get_param('survey', 'directory_list')
        return self.decode_dir_list(S)
    def set_survey_directory_list(self,dir_list,recursiveIndex):
        S = self.encode_dir_list(dir_list, recursiveIndex)
        return self.set_param('survey', 'directory_list',S)
    def get_installed_languages(self):
        return self.get_param('language', 'installed').split(',')
    def set_installed_languages(self,S):
        if hasattr(S, '__iter__') : S = ','.join(S)
        return self.set_param('language', 'installed',S)
    def get_current_language(self):
        return self.get_param('language', 'current')
    def set_current_language(self,S):
        return self.set_param('language', 'current',S)
    def get_current_scanner(self):
        return self.get_param('scanner', 'source')
    def set_current_scanner(self,S):
        return self.set_param('scanner', 'source',S)
    def get_database_name(self):
        return self.get_param('database', 'filename')
    def set_database_name(self,S):
        return self.set_param('database', 'filename',S)
    def get_resource_filename(self):
        return self.get_param('general', 'resourceFile')
    def get_ocr_confname(self):
        defConf = os.path.join(Resources.get_resource_dir(),'OCR.ini')
        return self.get_param('OCR', 'configurationFile',defConf,True)
    def get_ocr_configuration(self):
        return OCRConfiguration(self.get_ocr_confname())
    
    def encode_dir_list(self , dir_list , checked):
        answer = ""
        for i in range(len(dir_list)) :
            if i in checked : answer = answer + '*'
            answer = answer + dir_list[i] + '|'
        return answer
    def decode_dir_list(self,S):
        items_list = S.split('|')
        checked = []
        dir_list = []
        
        for item in items_list :
            item = item.strip()
            if len(item)<1 : continue
            if item[0] == '*' :
                checked.append(len(dir_list))
                item=item[1:]
            dir_list.append(item)
        return (dir_list , checked)


class Base(object):
    '''(
    this class is the interface between the application and the database engine
    )'''
    #===========================================================================
    # constants
    #===========================================================================
    documents_tableName = 'documents'
    keywords_tableName = 'keywords'
    docWords_tableName = 'docWords'
    persons_tableName = 'persons'
    params_tableName = 'parameters'
    folders_tableName='folders'
    folderDoc_tableName='folderDocs'
    
    param_DB_VERSION='DB_VERSION'
    DB_VERSION=1.2
    
    IDX_TITLE=0
    IDX_DESCRIPTION=1
    IDX_FILENAME=2
    IDX_REGISTER_DATE=3
    IDX_REGISTER_PERSON_ID=4
    IDX_DOCUMENT_DATE=5
    IDX_TAGS=6
    IDX_CHECKSUM=7
    IDX_ROWID=8
    
    ID_TAG=0
    ID_TITLE=1
    ID_DESCRIPTION=2
    ID_FULL_TEXT=3
    #===========================================================================
    # constructor
    #===========================================================================
    def __init__(self,base_name):
        '''
        Constructor
        '''
        self.use_base(base_name)
    def use_base(self,base_name):
        self.connexion = sqlite3.connect(base_name, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        self.base_name = base_name

    #===========================================================================
    # test if a table exists
    #===========================================================================
    def exist_table(self, base_name):
        '''(
        Test if a given table exists
        )'''
        try:
            cur = self.connexion.execute("SELECT name FROM sqlite_master WHERE name = '" + base_name + "' AND type='table' ;")
            return (cur and cur.arraysize>0)
        except:
            return False
    #===========================================================================
    # create the table
    #===========================================================================
    def create_table(self, table_name, structure):
        '''(
        Automatically create the asked table, if not already exists in the database
        )'''
        sql_statement = "CREATE TABLE IF NOT EXISTS " + table_name + "(" + structure + ")"
        try:
            self.connexion.execute(sql_statement)
            return True
        except:
            return False
    def win32_samefile(self,p1,p2):
        return os.path.abspath(p1).lower() == os.path.abspath(p2).lower()
    #===========================================================================
    # build the database
    #===========================================================================
    def buildDB(self):
        '''( 
        create the database (all the tables)
        database structures:
        documents = title,description,filename,registerDate,registerPersonId,documentDate,tags,checksum
        keywords = keyword(primary_key) , soundex_word (indexed)
        docWords = keyID,docID,field
        persons = name
        params = name , value
        folders = name,parentID
        foldDocs = docID,folderID
        )'''
        self.create_table(self.documents_tableName, 'title TEXT(64), description TEXT(256), filename TEXT(256), registerDate DATE, registeringPersonID INTEGER, documentDate DATE,tags TEXT,checksum TEXT')
        self.create_table(self.keywords_tableName, 'keyword TEXT PRIMARY KEY , soundex_word TEXT ')
        sql_statement = "CREATE INDEX IF NOT EXISTS SOUNDEX ON " + self.keywords_tableName + "(soundex_word)"
        try:
            self.connexion.execute(sql_statement)
        except:
            gui.utilities.show_message('Error during database index creation')
            
        #self.create_table(self.docWords_tableName, 'keyID INTEGER references ' + self.keywords_tableName + '(ROWID) ,docID INTEGER references ' + self.documents_tableName + '(ROWID)')
        self.create_table(self.docWords_tableName, 'keyID INTEGER  ,docID INTEGER, field INT,count INT default 1')
        self.create_table(self.persons_tableName, 'name TEXT')
        self.create_table(self.params_tableName, 'name TEXT , value TEXT')
        self.create_table(self.folders_tableName, 'name TEXT , parentID INT')
        self.create_table(self.folderDoc_tableName, 'docID INT , folderID INT')
        if os.name == 'nt' or os.name == 'win32' :
            self.connexion.create_function("IS_IN_DIR", 2, lambda fname,dirname : self.win32_samefile(os.path.dirname(fname), dirname))
        else:
            self.connexion.create_function("IS_IN_DIR", 2, lambda fname,dirname : os.path.samefile(os.path.dirname(fname), dirname))
        self.connexion.create_function("EXTENSION", 1, lambda fname : os.path.splitext(fname)[1])
        self.connexion.create_function("PHONEX", 1, lambda word : algorithms.words.phonex(word))
        db_version = self.get_parameter(self.param_DB_VERSION)
        if not db_version:
            self.set_parameter(self.param_DB_VERSION, self.DB_VERSION)
            db_version = self.get_parameter(self.param_DB_VERSION)
        db_version = float(db_version)
        if db_version > self.DB_VERSION:
            gui.utilities.show_message(_('Unstable state: Your database version is newer than the program itself...'))
            return False
        if db_version<1.1 :
            sql_statement = 'ALTER TABLE %s ADD COUNT INT default 1' % self.docWords_tableName
            try:
                self.connexion.execute(sql_statement)
            except Exception as E:
                gui.utilities.show_message('Error during database view creation : ' + str(E))
            sql_statement = 'DROP VIEW fullDoc'
            try:
                self.connexion.execute(sql_statement)
                self.connexion.commit()
            except:
                pass
        sql_statement = 'create view if not exists fullDoc as select D.title as title,D.description,D.filename,D.registerDate,D.registeringPersonID,D.documentDate,D.tags,D.checksum, D.RowID docID,K.keyword,K.soundex_word as soundex_word,DW.field,DW.count '
        sql_statement += 'FROM ' + self.keywords_tableName + ' K,' + self.documents_tableName + ' D,'
        sql_statement += self.docWords_tableName + ' DW'
        sql_statement += ' WHERE DW.keyID = K.rowID AND DW.docID = D.RowID'
        try:
            self.connexion.execute(sql_statement)
        except Exception,E:
            gui.utilities.show_message('Error during database view creation :' + str(E))
            return False
        
        self.set_parameter(self.param_DB_VERSION, self.DB_VERSION)
        return True
    
    #===========================================================================
    # set a parameter
    #===========================================================================
    def set_parameter(self,parameter_name,parameter_value):
        Q = 'SELECT value FROM ' + self.params_tableName +' WHERE name=?'
        try:
            cur = self.connexion.execute(Q,(parameter_name,))
            if not cur or not cur.fetchone():
                Q = 'INSERT INTO ' + self.params_tableName +' VALUES (?,?)'
                cur = self.connexion.execute(Q,(parameter_name,str(parameter_value)))
            else:
                Q = 'UPDATE ' + self.params_tableName +' SET value=? WHERE name=?'
                cur = self.connexion.execute(Q,(str(parameter_value),parameter_name))
            self.connexion.commit()
            return True
        except:
            return False
    #===========================================================================
    # get a parameter
    #===========================================================================
    def get_parameter(self,parameter_name):
        Q = 'SELECT value FROM ' + self.params_tableName +' WHERE name=?'
        try:
            cur = self.connexion.execute(Q,(parameter_name,))
            row = cur.fetchone()
            if row :
                return row[0]
            else:
                return None
        except :
            return None
         
    #===============================================================================
    # add a new document to the database
    #===============================================================================
    def add_document(self, fileName, title = 'untitled', description = '', registeringPerson = None\
                     , documentDate = None, keywordsGroups = None , tags = ''):
        '''(
        Add a new document to the database
        only the filename is mandatory
        the registering date is automatically taken from the system
        )'''
        docID = None
        registeringDate = datetime.date.today()
        cur = self.connexion.cursor()
        if not documentDate : documentDate = registeringDate
        personID = 0
        file_md5 = hashlib.md5(open(fileName, "rb").read()).hexdigest()

        # try to find the given person (if a value is given)
        if registeringPerson:
            sql_statement = 'SELECT ROWID FROM ' + self.persons_tableName + " WHERE name=?"
            try:
                cur = self.connexion.execute(sql_statement,(registeringPerson,))
                row = cur.fetchone()
                # if not found --> create the person in the database
                if not row:
                    sql_statement = "INSERT INTO " + self.persons_tableName + " VALUES (?)"
                    cur = self.connexion.execute(sql_statement,(registeringPerson,))
                    personID = cur.lastrowid
                else:
                    personID = row[0]
            except:
                gui.utilities.show_message(_('Unable to assign the registering person'))
                pass
        try:
            # add the document entry in the database
            #sql_statement = 'INSERT INTO ' + self.documents_tableName + " VALUES ('" + title + "','" + description + "','" + fileName + "','" + str(registeringDate) + "'," + str(personID) + ",'" + str(documentDate) + "','" + str(file_md5) + "')"
            sql_statement = 'INSERT INTO ' + self.documents_tableName + " VALUES (?,?,?,?,?,?,?,?)"
            cur = self.connexion.execute(sql_statement,(title,description,fileName,registeringDate,personID,documentDate,tags,str(file_md5)))
            docID = cur.lastrowid
        except:
            gui.utilities.show_message(_('Unable to add the document'))
            return False
        self.connexion.commit()
        if keywordsGroups :
            # find the list of keyword not yet registered
            if not self.update_keywords_for(docID,keywordsGroups) : return False
        return True # finishes if no keyword to register
    #===============================================================================
    # finding keywords rows
    #===============================================================================
    def find_keywords(self, keywords):
        '''(
        find all the rows of the keywords table corresponding to the given input
        keyword is a list of list of words
        ((word11,word12,...word1N1),(word21,word22,...word2N2),...,(wordM1,wordM2,...,wordMNM))
        means (word11 AND word12 AND ... AND word1N1) OR ... OR  (wordM1 AND wordM2 AND ... AND wordMNM)
        )'''
        cur = None
        if not keywords : return None
        keywords =  map(lambda s:algorithms.words.phonex(s) , keywords)
        # first : find the keyword in the keywords table
        if isinstance(keywords,list):
            Q = "SELECT ROWID FROM " + self.keywords_tableName + " WHERE soundex_word IN " + self.make_placeholder_list(len(keywords))
        else:
            Q = "SELECT ROWID FROM " + self.keywords_tableName + " WHERE soundex_word = ?"
        try:
            #print "finding keys via " + Q
            cur = self.connexion.execute(Q , keywords)
            return cur
        except:
            gui.utilities.show_message(_('Unable to search keywords'))
            return None


    #===============================================================================
    # find documents corresponding to the sql request
    #===============================================================================
    def find_sql(self,request,pars):
        if request=='': return self.find_documents(None)     
        try:
            sql_command = "SELECT docID FROM fullDoc WHERE " + request + " GROUP BY docID" 
#            print sql_command,pars
            cur = self.connexion.execute(sql_command,pars)
            rowIDList = self.rows_to_str(cur,0,'')
            sql_command = "SELECT *,ROWID FROM "+ self.documents_tableName + ' WHERE ROWID IN ' + str(rowIDList)
            cur = self.connexion.execute(sql_command)
            return cur
        except Exception as E:
            gui.utilities.show_message('SQL search failed ' + str(E))
            #print E 
            return None
    #===============================================================================
    # find tag entry starting by a given prefix and for an optional given field
    #===============================================================================
    def find_keywords_by_prefix(self,prefix='',field_num=None):
        try:
            sql_command = "SELECT rowID,keyword FROM " + self.keywords_tableName + " WHERE keyword LIKE ?" 
            cur = self.connexion.execute(sql_command,(prefix + '%' ,))
            if field_num is None:
                return [ row[1] for row in cur]
            else:
                keyXX = self.rows_to_str(cur,0,'')
                sql_command = "SELECT DISTINCT keyID from " + self.docWords_tableName + " WHERE keyID IN " + keyXX + " AND field = ?"
                cur = self.connexion.execute(sql_command,(field_num,))
                sql_command = "SELECT keyword FROM " + self.keywords_tableName + " WHERE rowID IN " + self.rows_to_str(cur,0,'')
                cur = self.connexion.execute(sql_command)
                return [ row[0].encode('utf-8') for row in cur]
        except Exception as E:
            gui.utilities.show_message('SQL search failed ' + str(E) )
            return None
    #===============================================================================
    # find entry starting by a given prefix and for a given field
    #===============================================================================
    def find_field_by_prefix(self,prefix='',field_str='title'):
        try:
            sql_command = "SELECT %s FROM %s WHERE %s LIKE ?" % (field_str,self.documents_tableName,field_str)
            p = prefix+'%'
            cur = self.connexion.execute(sql_command,(p,))
            return [ row[0].encode('utf-8') for row in cur]
        except Exception as E:
            gui.utilities.show_message('SQL search failed ' + str(E) )
            return None
    
    #===============================================================================
    # find documents corresponding to keywords
    #===============================================================================
    def find_documents(self, keywords = None,fields=None):
        '''(
        find all the document of the database that contain any of the given keywords
        keyword is a list of list of words
        ((word11,word12,...word1N1),(word21,word22,...word2N2),...,(wordM1,wordM2,...,wordMNM))
        means (word11 AND word12 AND ... AND word1N1) OR ... OR  (wordM1 AND wordM2 AND ... AND wordMNM)
        )'''
       
        cur = None
        sql_statement = 'SELECT *,ROWID FROM ' + self.documents_tableName
        if keywords:
            # first : find the keyword in the keyword table
            cur = self.find_keywords(keywords)
            if not cur or cur.arraysize<1: return None
            # if some keywords are found, find the corresponding doc lines
            lst = self.rows_to_str(cur)
            Q = "SELECT docID FROM " + self.docWords_tableName + " WHERE keyID IN " + lst
            if fields :
                Q += ' AND FIELD IN ' + self.make_placeholder_list(len(fields))
            #print Q
            try:
                if fields :
                    cur = self.connexion.execute(Q , fields)
                else:  
                    cur = self.connexion.execute(Q)
            except:
                gui.utilities.show_message(_('Keyword search failed'))
                return None
            # cur now contain the docID to take
            if cur:
                rowIDList = self.rows_to_str(cur)
                sql_statement += ' WHERE ROWID IN ' + str(rowIDList)
        try:
            cur = self.connexion.execute(sql_statement)
        except:
            gui.utilities.show_message(_('Document search failed'))
            return None
        return cur
    #===========================================================================
    # create a list with n placeholder (?,?,...?) 
    #===========================================================================
    def make_placeholder_list(self,n):
        ''' create a string (?,?,...,?) with n < ? > chars inside '''
        if n<1 : return '()'
        if n<2 : return '(?)'
        return '(' + '?,' * (n-1) + '?)'
    #===========================================================================
    # utility function transform the content of a python list into an (e1,e2,...) string format
    #===========================================================================
    def iterable_to_sqlStrList(self,iterable,stringChar='"'):
        ''' transform an iterable into a (E1,E2,...En) string, where Ei is the ith element of <iterable> '''
        if len(iterable)<1: return '()'
        sql_list = [ stringChar + str(i) + stringChar for i in iterable]
        sql_list = '(' + ','.join(sql_list) + ')'
        return sql_list
    #===========================================================================
    # utility function transform the content of a column from cur into a (e1,e2,...) string format
    #===========================================================================
    def rows_to_str(self,cur,idx=0,stringChar='"'):
        ''' utility function transform the content of a column from cur into a (e1,e2,...) string format '''
        return self.iterable_to_sqlStrList([x[idx] for x in cur],stringChar)
    #===========================================================================
    # return the list of keywords absent from the database
    #===========================================================================
    def find_absent_keywords(self,keywords):
        ''' return the list of keywords absent from the database '''
#        keywords_str = [ '"' + i + '"' for i in keywords]
#        keywords_str = '(' + ','.join(keywords_str) + ')'
        
        Q = 'SELECT keyword FROM ' + self.keywords_tableName + ' WHERE keyword IN ' + self.make_placeholder_list(len(keywords))
        try:
            cur = self.connexion.execute(Q,keywords)
            already_present = [ i[0] for i in cur]
        except:
            gui.utilities.show_message(_('Keyword search failed'))
            already_present = [ ]
        absents = [ s for s in keywords if s not in already_present]
        return list(set(absents))
    #===========================================================================
    # remove_document : remove the selected documents (docID must be a list of ids)
    # and all the keys referencing it
    #===========================================================================
    def remove_documents(self,docID):
        # first find and delete all the corresponding lines in keyword index
        Q = 'DELETE FROM ' + self.docWords_tableName + ' WHERE docID IN ' + self.make_placeholder_list(len(docID))
        try:
            self.connexion.execute(Q,docID)
        except:
            gui.utilities.show_message(_('Unable to remove documents/word associations'))
            return
        # then delete the documents entries themselves
        Q = 'DELETE FROM ' + self.documents_tableName + ' WHERE ROWID IN ' + self.make_placeholder_list(len(docID))
        try:
            self.connexion.execute(Q,docID)
            self.connexion.commit()
        except:
            gui.utilities.show_message(_('Unable to remove documents entries'))
            return
    #===========================================================================
    # update_keywords_for : remove all the keyword reference to docID
    # and  replace by a new list
    #===========================================================================
    def update_keywords_for(self,docID,keywordsGroups,keepFullTextIfNotGiven=True):
        # first : delete all the keyword references to docID
        if not hasattr(docID,'__iter__') : docID = (docID,)
        hasFullText = False
        for iField in range(len(keywordsGroups)) :
            if keywordsGroups[iField][0] == self.ID_FULL_TEXT :
                hasFullText=True
                break
        Q = 'DELETE FROM ' + self.docWords_tableName + ' WHERE docID IN ' + self.make_placeholder_list(len(docID))
        if keepFullTextIfNotGiven and not hasFullText :
            Q = Q+' AND field <> ' + str(self.ID_FULL_TEXT)
        try:
            #print Q
            self.connexion.execute(Q,docID)
        except:
            gui.utilities.show_message(_('Unable to remove doc/word association'))
            return False
        for iField in range(len(keywordsGroups)) :
            keyGroup = keywordsGroups[iField]
            field = keyGroup[0]
            # add all absent keywords to the keywords table
            if type(keyGroup[1]) is list:
                all_keywords = dict([ (item.lower(),keyGroup[1].count(item)) for item in keyGroup[1] ])
            elif type(keyGroup[1]) is dict:
                all_keywords = dict([ (item.lower(),weight) for item,weight in keyGroup[1].items() ])
            absents = self.find_absent_keywords(all_keywords.keys())
            absents = map(lambda x:(x,algorithms.words.phonex(x)) , absents)
            Q = 'INSERT INTO ' + self.keywords_tableName + ' VALUES (?,?)'
            try:
                self.connexion.executemany(Q,absents)
            except  Exception,E:
                gui.utilities.show_message(_('Unable to insert new keywords : ') + str(E))
                return False
            # get back all the keyword IDs for the current field
            Q = 'SELECT ROWID,KEYWORD FROM ' + self.keywords_tableName + ' WHERE keyword IN ' + self.make_placeholder_list(len(all_keywords))
            addedKeys = []
            try:
                cur = self.connexion.execute(Q,all_keywords.keys())
                addedKeys = [ (row[0],all_keywords[row[1].lower()]) for row in cur]
            except:
                gui.utilities.show_message(_('Unable to search for keywords'))
                return False
            # add the new keyID to the table
            for adoc_i in docID:
                #word_count=1 # TODO UPDATE COUNTERS
                #Q = 'INSERT INTO ' + self.docWords_tableName + ' VALUES (?,' +  str(adoc_i) + ',' + str(field) + ',' + str(word_count) + ')'
                Q = 'INSERT INTO ' + self.docWords_tableName + ' VALUES (?,' +  str(adoc_i) + ',' + str(field) + ',?)'
                try:
                    self.connexion.executemany(Q , addedKeys)
                except:
                    gui.utilities.show_message(_('Unable to insert new document/word association'))
                    return False
            try:
                self.connexion.commit()
            except:
                return False
        return True
    
    #===========================================================================
    # update_doc : replace the values for a given doc
    #===========================================================================
    def update_doc(self,docID,title,description,documentDate,filename,tags,fullText=None):
        Q = 'UPDATE ' + self.documents_tableName + ' SET title=? , description=?, documentDate=? ,tags=? , filename=? WHERE ROWID=?'
        try:
            self.connexion.execute(Q,(title,description,documentDate,tags,filename,docID))
            self.connexion.commit()
        except:
            gui.utilities.show_message(_('Unable to update document into database'))
            return
        keywordsGroups = self.get_keywordsGroups_from(title, description, filename,tags,fullText)
        return self.update_keywords_for(docID,keywordsGroups)
    #===========================================================================
    # update_doc : replace the values for a given doc
    #===========================================================================
    def update_doc_signature(self,docID,file_md5):
        Q = 'UPDATE ' + self.documents_tableName + ' SET checksum=? WHERE ROWID=?'
        try:
            self.connexion.execute(Q,(file_md5,docID))
            self.connexion.commit()
        except:
            gui.utilities.show_message(_('Unable to reassign checksum into database entry'))
            return False
        return True
    #===========================================================================
    # get_keywords_from : find the keywords from a document
    #===========================================================================
    def get_keywordsGroups_from(self,title,description,filename,tags,fullText=None):  
        keywords_title = string.split(title, ' ')
        keywords_title = [i.lower() for i in keywords_title if len(i)>3 and i.isalpha()]
        
        keywords_descr = string.split(description, ' ')
        keywords_descr = [i.lower() for i in keywords_descr if len(i)>3 and i.isalpha()]
        
        keywords_tag = string.split(tags , ',')
        keywords_tag =  map(lambda s:s.lower() , keywords_tag)
        
        if fullText is None:
            return ( ( self.ID_TITLE, keywords_title) , (self.ID_DESCRIPTION , keywords_descr) , (self.ID_TAG ,keywords_tag ) )
        else:
            return ( ( self.ID_TITLE, keywords_title) , (self.ID_DESCRIPTION , keywords_descr) , (self.ID_TAG ,keywords_tag ) ,(self.ID_FULL_TEXT,fullText) )
    #===========================================================================
    # get_files_under : retrieve all the documents of the database whose filename
    # are on the directory <directory> (directly and not under subdir)
    #===========================================================================
    def get_files_under(self,directory,acceptedExt=None):
        if acceptedExt:
            Q = "SELECT filename FROM " + self.documents_tableName + " WHERE IS_IN_DIR(filename,?) AND EXTENSION(filename) IN " + self.make_placeholder_list(len(acceptedExt))
        else:
            Q = "SELECT filename FROM " + self.documents_tableName + " WHERE IS_IN_DIR(filename,?) "
        try:
            if acceptedExt:
                acceptedExt = [ i for i in acceptedExt];
                acceptedExt.insert(0, directory)
                cur = self.connexion.execute(Q,acceptedExt)
            else:
                cur = self.connexion.execute(Q,(directory,))
            return cur
        except:
            #gui.utilities.show_message('Unable to get file list from database')
            return ()
    #===========================================================================
    # get_all_keywords : retrieve all the recorded keywords
    #===========================================================================
    def get_all_keywords(self):
        Q = "SELECT keyword FROM " + self.keywords_tableName
        try:
            cur = self.connexion.execute(Q)
            return tuple([row[0].encode('utf-8').lower() for row in cur])
        except:
            return ()
    #===========================================================================
    # doc_without_ocr : retrieve all docs without any OCR term recored
    #===========================================================================
    def doc_without_ocr(self):
        Q = "select distinct docID from %s except select distinct docID from %s where field=%d" %(self.docWords_tableName,self.docWords_tableName,self.ID_FULL_TEXT)
        try:
            cur = self.connexion.execute(Q)
            rowIDList = self.rows_to_str(cur,0,'')
            sql_command = "SELECT *,ROWID FROM "+ self.documents_tableName + ' WHERE ROWID IN ' + str(rowIDList)
            cur = self.connexion.execute(sql_command)
            return cur
        except:
            return ()
    #===========================================================================
    # folders_childs_of(ID) : retrieve all folders whose parent is ID
    #===========================================================================
    def folders_childs_of(self,ID):
        Q = 'select rowID,name from %s where parentID==?' % self.folders_tableName 
        try:
            cur = self.connexion.execute(Q, [ID,])
            return cur
        except:
            return ()
    #===========================================================================
    # folders_add_child_under(name,ID) : add a child named name under folder ID
    #===========================================================================
    def folders_add_child_under(self,name,ID):
        Q = 'INSERT INTO %s VALUES (?,?)' % self.folders_tableName 
        try:
            cur = self.connexion.execute(Q, [name,ID])
            self.connexion.commit()
            return True
        except:
            return False
    #===========================================================================
    # folders_remove(ID) : remove a folder from database 
    #===========================================================================
    def folders_remove(self,ID):
        try:
            Q = 'DELETE FROM %s WHERE folderID=?' % self.folderDoc_tableName
            self.connexion.execute(Q, [ID,])
            Q = 'DELETE FROM %s WHERE rowID=?' % self.folders_tableName 
            cur = self.connexion.execute(Q, [ID,])
            self.connexion.commit()
            return True
        except:
            return False
    #===========================================================================
    # folders_rename(ID,name) : rename the folder ID with name <name> 
    #===========================================================================
    def folders_rename(self,ID,name):
        try:
            Q = 'UPDATE %s SET name=? WHERE rowID=?' % self.folders_tableName 
            cur = self.connexion.execute(Q, [name,ID])
            self.connexion.commit()
            return True
        except:
            return False
    #===========================================================================
    # folders_genealogy_of(folderID) : return the parent, grandparent, grand-grand parents,... of a folder
    #===========================================================================
    def folders_genealogy_of(self,folderID):
        genealogy = []
        try:
            cont=True
            while cont:
                Q = 'SELECT parentID FROM %s WHERE rowID=?' % self.folderDoc_tableName 
                cur = self.connexion.execute(Q, [folderID,])
                parent = cur[0][0]
                genealogy.append(parent)
                cont = (parent != 0)
        except:
            return []
    #===========================================================================
    # folders_is_descendant_of(folderID,baseID) : does folder folderID in the descendant of parentID
    #===========================================================================
    def folders_is_descendant_of(self,folderID,baseID):
        genealogy = self.folders_genealogy_of(folderID)
        return folderID in genealogy
    #===========================================================================
    # folders_does_doc_descendant_from(docID,baseID) : does doc docID in the descendant of parentID
    #===========================================================================
    def folders_does_doc_descendant_from(self,docID,baseID):
        try:
            Q = 'SELECT folderID FROM %s WHERE docID =?' % self.folderDoc_tableName
            cur = self.connexion.execute(Q, [docID])
            folderIDs = [row[0] for row in cur]
        except:
            foldersID=[]
        for folderID in folderIDs:
            genealogy = self.folders_genealogy_of(folderID)
            if (folderID in genealogy) : return True
        return False
    #===========================================================================
    # folders_add_doc_to(docID,folderID) : add the document docID under the folder ID 
    #===========================================================================
    def folders_add_doc_to(self,docID,folderID):
        try:
            Q = 'INSERT INTO %s VALUES (?,?)' % self.folderDoc_tableName
            cur = self.connexion.execute(Q, [docID,folderID])
            self.connexion.commit()
            return True
        except:
            return False
    #===========================================================================
    # folders_rem_doc_from(docID,folderID) : remove the document docID under the folder ID 
    #===========================================================================
    def folders_add_doc_to(self,docID,folderID):
        try:
            Q = 'DELETE FROM %s WHERE docID=? AND folderID=?' % self.folderDoc_tableName 
            cur = self.connexion.execute(Q, [docID,folderID])
            self.connexion.commit()
            return True
        except:
            return False
            

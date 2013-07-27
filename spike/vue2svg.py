"""
vue2svg : spike/prototype for scenetool.
generates an svg scene from VUE files specified on command line.

usage:

 python3.2 vue2svg.py ../test/vue/*.vue


https://github.com/tangentstorm/scenetool
copyright (c) 2013 michal j wallace.
available to the public under the MIT/x11 license. (see ../LICENSE)
"""
import os, sys, io, itertools as it
from collections import namedtuple
import sqlite3

from lxml import etree


DB_PATH = "vuedata.sdb" # note: will be wiped out on each run!

nsmap = {
    'xsi':"http://www.w3.org/2001/XMLSchema-instance"
}

def xp(tree, path):
    match = tree.xpath(path, namespaces=nsmap)
    return match[0] if match else ''

VueData = namedtuple('VueData',
                  ('parent ntype shape id ts x y w h text layer autosized'
                   ' fill strokewidth strokecolor strokestyle textcolor'
                   ' font id1 id2 p0x p0y p1x p1y ctrlcount arrowstate'
                   ' c0x c0y c1x c1y').split( ))

def walk(tree, parent=0):
    """
    walk the tree recursively, extracting node data
    """
    children = tree.xpath('child')
    for child in children:
        row = VueData(*([parent] +
            [xp(child, path) for path in [
                '@xsi:type',
                'shape/@xsi:type',
                '@ID',
                '@created',
                '@x',
                '@y',
                '@width',
                '@height',
                '@label',
                '@layerID',
                '@autoSized',
                'fillColor/text()',
                'strokeWidth/text()',
                'strokeColor/text()',
                'strokeStyle/text()',
                'textColor/text()',
                'font/text()',
                'ID1/text()',
                'ID2/text()',
                'point1/@x',
                'point1/@y',
                'point2/@x',
                'point2/@y',
                '@controlCount',
                '@arrowState',
                'ctrlPoint0/@x',
                'ctrlPoint0/@y',
                'ctrlPoint1/@x',
                'ctrlPoint1/@y' ]]))
        yield row
        for item in walk(child, row.id): yield item


def load(dbc, filename):
    """
    load data from the vue file into the database
    """
    # vue files are not valid xml because the doctype is misplaced.
    # so to fix, just strip off the opening comments:
    data = open(filename, 'r').read()
    data = data[data.find('<?xml'):]
    vue = etree.parse(io.BytesIO(bytes(data, 'ascii')))

    cur = dbc.cursor()
    cur.execute('insert into file values (?)', [filename])
    fid = cur.lastrowid

    for row in walk(vue, 0):
        sql = 'insert into vuedata values (? %s)' \
            % (', ? ' * len(VueData._fields))
        cur.execute(sql, [fid] + list(row))


def connect():
    return sqlite3.connect(DB_PATH, isolation_level=None) # autocommit

def main(filenames):

    if os.path.exists(DB_PATH): os.unlink(DB_PATH)
    dbc = connect()
    cur = dbc.cursor()
    cur.execute('create table if not exists file (filename string)')

    sql = 'create table if not exists vuedata (fid integer, %s)' \
        % ', '.join('%s data' % col for col in VueData._fields)
    cur.execute(sql)

    for filename in filenames:
        load(dbc,filename)

    dbc.close()

    # run the scripts and check for error (non-zero exit code)
    if ( os.system("sqlite3 %s < schema.sql" % DB_PATH)
       + os.system("sqlite3 %s < vue2elem.sql" % DB_PATH)
       + os.system("sqlite3 %s < views.sql" % DB_PATH)
       ) > 0: sys.exit()

    dbc = connect()
    cur = dbc.cursor()

    cur.execute("select * from file, vuedata "
                "where file.rowid = vuedata.fid "
                "order by file.rowid")
    lastfile = None
    for filename, rows in it.groupby(cur.fetchall(), lambda r: r[0]):
        print('##', filename, '#' * (60-len(filename)))
        for row in rows:
            print(';'.join(map(str,row[1:])))

if __name__=="__main__":
    if len(sys.argv) > 1: main(sys.argv[1:])
    else: print(__doc__)

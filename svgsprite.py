#!/usr/bin/python2
#coding=utf-8
import sys
import argparse
from xml.dom.minidom import parse
from xml.parsers.expat import ExpatError

parser = argparse.ArgumentParser(description='Convert SVG file to ninja SVG sprite')
parser.add_argument('filename', help="SCG file to process")
parser.add_argument('--id-prefix', default=None, help="If specified only ids with this prefix will be processed")
parser.add_argument('--ids', default=None, help="Coma-separated list. If specified only these ids will be processed")
args = parser.parse_args()
if(args.ids):
	args.ids = [x.strip() for x in args.ids.split(',')]
if(args.ids and args.id_prefix):
	print "Please specify either id-prefix or ids but not both."
	sys.exit()

try:
	xml = parse(args.filename)
except IOError:
	print "Could not find file \"%s\"" % args.filename
	sys.exit()
except ExpatError:
	print "Could not parse file \"%s\". Is this a valid svg file?" % args.filename
	sys.exit()

groups = xml.getElementsByTagName('g')
for g in groups:
	gid = g.getAttribute('id')
	if(args.ids and gid in args.ids):
		g.setAttribute('class', 'sprite')
	elif(args.id_prefix and gid.startswith(args.id_prefix)):
		g.setAttribute('class', 'sprite')
	elif(not (args.ids or args.id_prefix)):
		g.setAttribute('class', 'sprite')

svg = xml.getElementsByTagName('svg')
defs = xml.createElement('defs')
style = xml.createElement('style')
styleText = xml.createTextNode("svg .sprite { display: none }\nsvg .sprite:target { display: inline } ")
style.appendChild(styleText)
defs.appendChild(style)
svg[0].appendChild(defs)

print xml.toxml()

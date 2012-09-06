#!/usr/bin/python2
#coding=utf-8
import sys
import argparse
from xml.dom.minidom import parse, parseString
from xml.parsers.expat import ExpatError
import os
from decimal import *
import subprocess

scour_path = os.path.abspath('svg-scour')
sys.path.append(scour_path)
from scour import scourString, _options_parser, serializeTransform
from svg_transform import svg_transform_parser


def which(program):

	def is_exe(fpath):
		return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

	fpath, fname = os.path.split(program)
	if fpath:
		if is_exe(program):
			return program
	else:
		for path in os.environ["PATH"].split(os.pathsep):
			exe_file = os.path.join(path, program)
			if is_exe(exe_file):
				return exe_file

	return None


def readin_xml(filename):
	try:
		xml = parse(args.filename)
	except IOError:
		print "Could not find file \"%s\"" % args.filename
		sys.exit()
	except ExpatError:
		print "Could not parse file \"%s\". Is this a valid svg file?" % args.filename
		sys.exit()
	return xml

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Convert SVG file to ninja-style SVG sprite. Default behaviour is to find all elements with matching ids, move them to 0,0, resize the document viewbox to the width & height of the largest identified items, add a css-based trick to allow targeting sprites with hash in the url and finally use scour to shave off some bytes from the svg prior to outpiting it to stdout.')
	parser.add_argument('filename', help="SCG file to process")
	parser.add_argument('--id-prefix', default=None, help="If specified only ids with this prefix will be processed")
	parser.add_argument('--ids', default=None, help="Coma-separated list. If specified only these ids will be processed")
	parser.add_argument('--skip-scour',  action='store_true', default=False, help="If specified document won't be stripped & viewboxed using scour")
	parser.add_argument('--skip-positioning', action='store_true', default=False, help="If specified all matched groups won't positioned at 0,0")
	parser.add_argument('--dont-strip-comments', action='store_true', default=False, help="If specified comments won't be stripped. Has no effect when using --skip-scour")
	parser.add_argument('--dont-remove-metadata', action='store_true', default=False, help="If specified metadata from the document won't be stripped. Has no effect when using --skip-scour")
	parser.add_argument('--disable-viewboxing', action='store_true', default=False, help="If specified sizing/viewboxing won't be performed. Has no effect when using --skip-scour")
	parser.add_argument('--disable-viebox-resizing', action='store_true', default=False, help="If specified viewbox resizing won't be performed. Depending on the input svg file might not work in some cases when used in conjuction with '--disable-viewboxing' or '--skip-scour'. In most cases makes no sense when used in conjuction with '--skip-positioning'")

	args = parser.parse_args()
	if(args.ids):
		args.ids = [x.strip() for x in args.ids.split(',')]
	if(args.ids and args.id_prefix):
		print "Please specify either id-prefix or ids but not both."
		sys.exit()

	inkscape = None
	if(not args.skip_positioning):
		inkscape = which('inkscape')
		if(inkscape == None):
			print "Could not find inkscape in system path. Either install inkscape (http://inkscape.org/) or disable positioning with --skip-positioning"
			sys.exit()
		xml = readin_xml(args.filename)

	items = []
	for svgtag in ["a", "altGlyph", "altGlyphDef", "altGlyphItem", "animate", "animateColor", "animateMotion", "path", "animateTransform", "circle", "clipPath", "color-profile", "cursor", "defs", "desc", "ellipse", "feBlend", "filter-primitive-reference", "g", "image", "line", "linearGradient", "marker", "mask", "path", "pattern", "polygon", "polyline", "radialGradient", "rect", "stop", "text", "tref", "tspan", "text", "use"]:
		items = items + xml.getElementsByTagName(svgtag)

	maxwidth = 0
	maxheight = 0
	for g in items:
		gid = g.getAttribute('id')
		if(args.ids and gid in args.ids
			or args.id_prefix and gid.startswith(args.id_prefix)
			or not (args.ids or args.id_prefix)):
			g.setAttribute('class', 'sprite')
			if(not args.skip_positioning):

				# this will be massively slow
				offsetx = float(subprocess.check_output(['inkscape', '-z', '-X', '--query-id=%s' % gid, args.filename]))
				offsety = float(subprocess.check_output(['inkscape', '-z', '-Y', '--query-id=%s' % gid, args.filename]))
				width = float(subprocess.check_output(['inkscape', '-z', '-W', '--query-id=%s' % gid, args.filename]))
				height = float(subprocess.check_output(['inkscape', '-z', '-H', '--query-id=%s' % gid, args.filename]))

				if(width > maxwidth):
					maxwidth = width
				if(height > maxheight):
					maxheight = height

				if(offsety == 0 and offsetx == 0):
					g.setAttribute('transform', "translate(-%f,-%f)" % (offsetx, offsety))
				if(offsety > 0 or offsetx > 0):
					val = g.getAttribute('transform')
					translated = False
					if(val != ''):
						transform = svg_transform_parser.parse(val)
						for t in transform:
							if(t[0] == 'translate'):
								t[1][0] = (offsetx - float(t[1][0])) * -1
								t[1][1] = (offsety - float(t[1][1])) * -1
								translated = True
					if(translated):
						new_transform = serializeTransform(transform)
						g.setAttribute('transform', new_transform)
					else:
						g.setAttribute('transform', "translate(-%f,-%f)" % (offsetx, offsety))

	if(not args.skip_scour):
		options = _options_parser.get_default_values()

		options.strip_comments = not args.dont_strip_comments
		options.remove_metadata = not args.dont_remove_metadata
		options.enable_viewboxing = not args.disable_viewboxing
		options.indent_type = 'none'
		in_string = ''
		if(xml):
			in_string = xml.toxml()
		else:
			in_string = file(args.filename).read()
		out_string = scourString(in_string, options)
		xml = parseString(out_string)
	elif(not xml):
		xml = readin_xml(args.filename)

	svg = xml.getElementsByTagName('svg')[0]
	if(not args.disable_viebox_resizing):
		viewbox = '0 0 %f %f' % (maxwidth, maxheight)
		svg.setAttribute('viewBox', viewbox)

	defs = xml.createElement('defs')
	style = xml.createElement('style')
	styleText = xml.createTextNode("svg .sprite { display: none }\nsvg .sprite:target { display: inline } ")
	style.appendChild(styleText)
	defs.appendChild(style)
	svg.appendChild(defs)

	print >>sys.stdout, xml.toxml()

"""\
This overlay draws Star Systems on the Starmap.
"""
# Python imports
from math import *

import numpy as N

# wxPython imports
import wx
from extra.wxFloatCanvas.FloatCanvas   import Point, Group, Line
from extra.wxFloatCanvas.RelativePoint import RelativePoint, RelativePointSet
from extra.wxFloatCanvas.PolygonStatic import PolygonArrow, PolygonShip

# tp imports
from tp.netlib.objects                        import Object
from tp.netlib.objects.ObjectExtra.Universe   import Universe
from tp.netlib.objects.ObjectExtra.Galaxy     import Galaxy
from tp.netlib.objects.ObjectExtra.StarSystem import StarSystem
from tp.netlib.objects.ObjectExtra.Planet     import Planet
from tp.netlib.objects.ObjectExtra.Fleet      import Fleet

from Overlay   import SystemLevelOverlay, Holder
from Colorizer import *

def FindChildren(cache, obj):
	"""
	Figure out all the children of this object.
	"""
	if not isinstance(obj, Object):
		raise TypeError("Object must be an object not %r" % obj)

	kids = set()
	for cid in obj.contains:
		child = cache.objects[cid]

		kids.update(FindChildren(cache, child))
		kids.add(child)

	return list(kids)

def FindOwners(cache, obj):
	"""
	Figure out the owners of this oidect (and it's children).
	"""
	if not isinstance(obj, Object):
		raise TypeError("Object must be an object not %r" % obj)

	owners = set()
	for child in [obj]+FindChildren(cache, obj):
		if not hasattr(child, 'owner'):
			continue

		if child.owner in (0, -1):
			continue
		owners.add(child.owner)
	return list(owners)

def FindPath(cache, obj):
	"""
	Figure out the owners of this oidect (and it's children).
	"""
	if not isinstance(obj, Object):
		raise TypeError("Object must be an object not %r" % obj)

	locations = [obj.pos]
	for order in cache.orders[obj.id]:
		if order._name in ("Move", "Move To", "Intercept"):
			if hasattr(order, "pos"):
				locations.append(order.pos)
			if hasattr(order, "to"):
				locations.append(cache.objects[order.to].pos)
	if len(locations) == 1:
		return None
	return locations

class IconMixIn:
	"""
	"""
	PrimarySize = 3
	ChildSize   = 3

	def __init__(self, cache, colorizer):
		self.cache = cache
		self.SetColorizer(colorizer)

	# FIXME: Should probably just monkey patch this onto Group?
	def XY(self):
		return self.ObjectList[0].XY
	XY = property(XY)

	def GetSize(self):
		return (self.PrimarySize*2, self.PrimarySize*2)

	def ChildOffset(self, i):
		num = len(self.children)

		angle = ((2.0*pi)/num)*(i-0.125)
		return (int(cos(angle)*6), int(sin(angle)*6))

	def SetColorizer(self, colorizer):
		if not isinstance(colorizer, Colorizer):
			raise TypeError('Colorizer must be of Colorizer type!')
		self.Colorizer = colorizer

	def GetColors(self):
		parentcolor = self.Colorizer(FindOwners(self.cache, self.primary))
		
		childrencolors = []
		for child in self.children:
			childrencolors.append(self.Colorizer(FindOwners(self.cache, child)))
	
		return parentcolor, childrencolors

class SystemIcon(Group, Holder, IconMixIn):
	"""
	Display a round dot with a dot for each child.
	"""
	def copy(self):
		# FIXME: Very expensive
		return SystemIcon(self.cache, self.primary, self.Colorizer)

	def __init__(self, cache, system, colorizer=None):
		if not isinstance(system, StarSystem):
			raise TypeError('SystemIcon must be given a StarSystem, %r' % system)

		Holder.__init__(self, system, FindChildren(cache, system))

		# Get the colors of the object
		IconMixIn.__init__(self, cache, colorizer)
		type, childtype = self.GetColors()

		# Create a list of the objects
		ObjectList = []

		# The center point
		ObjectList.append(Point(system.pos[0:2], type, self.PrimarySize, False))

		if len(self.children) > 0:
			# The orbit bits
			ObjectList.insert(0, Point(system.pos[0:2], "Black", 8))
			ObjectList.insert(0, Point(system.pos[0:2], "Grey",  9, False))
	
			# The orbiting children
			for i, childtype in enumerate(childtype):
				ObjectList.append(
					RelativePoint(system.pos[0:2], childtype, self.ChildSize, False, self.ChildOffset(i))
				)

		Group.__init__(self, ObjectList, False)

class FleetIcon(Group, Holder, IconMixIn):
	"""
	Display a little arrow shape thing.
	"""
	def copy(self):
		# FIXME: Very expensive
		return FleetIcon(self.cache, self.primary, self.Colorizer)

	def __init__(self, cache, fleet, colorizer=None):
		if not isinstance(fleet, Fleet):
			raise TypeError('FleetIcon must be given a Fleet, %r' % system)

		if len(FindChildren(cache, fleet)) > 0:
			raise TypeError('The fleet has children! WTF?')

		Holder.__init__(self, fleet, [])

		# Get the colors of the object
		IconMixIn.__init__(self, cache, colorizer)
		type, childtype = self.GetColors()

		# Create a list of the objects
		ObjectList = []

		# The little ship icon
		ObjectList.append(PolygonShip(fleet.pos[0:2], type))

		Group.__init__(self, ObjectList, False)

class Systems(SystemLevelOverlay):
	name     = "Systems"
	toplevel = Galaxy, Universe

	Colorizers = [ColorVerses, ColorEach]

	def __init__(self, parent, canvas, panel, cache, *args, **kw):
		SystemLevelOverlay.__init__(self, parent, canvas, panel, cache, *args, **kw)

		self.canvas.SetCursor(wx.StockCursor(wx.CURSOR_RIGHT_ARROW))

		# Create a drop-down on the panel for colorizer
		self.ColorizeMode = wx.Choice(panel)
		self.ColorizeMode.Bind(wx.EVT_CHOICE, self.OnColorizeMode)

		# Populate the colorizer dropdown with information
		for colorizer in self.Colorizers:
			self.ColorizeMode.Append(colorizer.name, colorizer)
		self.ColorizeMode.SetSelection(0)

		self.Colorizer = None
		self.OnColorizeMode(None)

		sizer = wx.FlexGridSizer(10)
		sizer.AddGrowableRow(0)
		sizer.Add(self.ColorizeMode, proportion=1, flag=wx.EXPAND)
		panel.SetSizer(sizer)

	def OnColorizeMode(self, evt):
		cls = self.ColorizeMode.GetClientData(self.ColorizeMode.GetSelection())

		if not isinstance(self.Colorizer, cls):
			# Change the colorizer
			self.Colorizer = cls(self.cache.players[0].id)

			if not evt is None:
				self.CleanUp()
				self.UpdateAll()
				self.canvas.Draw()

	def UpdateAll(self):
		SystemLevelOverlay.UpdateAll(self)

		self['preview-arrow'] = PolygonArrow((0,0), "#555555", True)
		self['preview-arrow'].Hide()
		self['selected-arrow'] = PolygonArrow((0,0), "Red", True)

	def Icon(self, obj):
		if isinstance(obj, Fleet):
			return FleetIcon(self.cache, obj, self.Colorizer)
		else:
			return SystemIcon(self.cache, obj, self.Colorizer)

	def ArrowTo(self, arrow, icon, object):
		arrow.SetPoint(icon.primary.pos[0:2])
		arrow.SetOffset((0,0))

		i = icon.index(object)
		if i > 0:
			arrow.SetOffset(icon.ChildOffset(i-1))

	def ObjectLeftClick(self, icon, obj):
		"""
		Move the red arrow to the current object.
		"""
		self.ArrowTo(self['selected-arrow'], icon, obj)
		self.canvas.Draw()
		return True

	def ObjectHoverEnter(self, icon, pos):
		"""
		The pop-up contains details about what is in the system.
		Also draws the path of each object in the system.
		"""
		SystemLevelOverlay.ObjectHoverEnter(self, icon, pos)

		# Draw the path of the object
		paths = []
		for i, cobj in enumerate(icon):
			path = FindPath(self.cache, cobj)
			if path:
				pr = path[0]
				for p in path[1:]:
					paths.append(Line([pr[0:2], p[0:2]], LineColor='Blue', InForeground=True))
					pr = p

		if len(paths) > 0:
			self['paths'] = paths
			self.canvas.Draw()

	def ObjectHovering(self, icon, object):
		SystemLevelOverlay.ObjectHovering(self, icon, object)

		self['preview-arrow'].Show()
		self.ArrowTo(self['preview-arrow'], icon, object)
		self.canvas.Draw()

		return True

	def ObjectHoverLeave(self, icon):
		SystemLevelOverlay.ObjectHoverLeave(self, icon)

		# Hide any paths which are showing
		if self.has_key('paths'):
			del self['paths']
		self['preview-arrow'].Hide()
		self.canvas.Draw()

	def ObjectPopupText(self, icon):
		# Build the string
		s = "<font size='%s'>" % wx.local.normalFont.GetPointSize()
		for i, cobj in enumerate(icon):
			# Italics the currently selected object
			style = 'normal'
			if self.Selected != None and self.Selected.current == cobj:
				style = 'italic'

			color = icon.Colorizer(FindOwners(self.cache, cobj))

			s += "<font style='%s' color='%s'>%s" % (style, color, cobj.name)
			if isinstance(cobj, Fleet):
				for shipid, amount in cobj.ships:
					s+= "\n  %s %ss" % (amount, self.cache.designs[shipid].name)
			s += "</font>\n"

		s = s[:-1]+"</font>"

		return s


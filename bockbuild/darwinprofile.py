import os
import shutil
from plistlib import Plist
from util import *
from unixprofile import UnixProfile

class DarwinProfile (UnixProfile):
	def __init__ (self):
		UnixProfile.__init__ (self)
		
		self.name = 'darwin'
		self.mac_sdk_path = '/Developer/SDKs/MacOSX10.5.sdk'
		
		if not os.path.isdir (self.mac_sdk_path):
			raise IOError ('Mac OS X SDK does not exist: %s' \
				% self.mac_sdk_path)

		self.gcc_arch_flags = [ '-m32', '-arch i386' ]
		self.gcc_flags.extend ([
			'-D_XOPEN_SOURCE',
			'-isysroot %{mac_sdk_path}',
			'-mmacosx-version-min=10.5'
		])
		self.gcc_flags.extend (self.gcc_arch_flags)
		self.ld_flags.extend (self.gcc_arch_flags)

		self.env.set ('CC',  'gcc-4.2')
		self.env.set ('CXX', 'g++-4.2')

	def bundle (self):
		self.make_app_bundle ()

	def make_app_bundle (self):
		plist_path = os.path.join (self.bundle_skeleton_dir, 'Contents', 'Info.plist')
		app_name = 'Unknown'
		plist = None
		if os.path.exists (plist_path):
			plist = Plist.fromFile (plist_path)
			app_name = plist['CFBundleExecutable']
		else:
			print 'Warning: no Contents/Info.plist in .app skeleton'

		self.bundle_app_dir = os.path.join (self.bundle_output_dir, app_name + '.app')
		self.bundle_contents_dir = os.path.join (self.bundle_app_dir, 'Contents')
		self.bundle_res_dir = os.path.join (self.bundle_contents_dir, 'Resources')
		self.bundle_macos_dir = os.path.join (self.bundle_contents_dir, 'MacOS')

		# Create the .app tree, copying the skeleton
		shutil.rmtree (self.bundle_app_dir, ignore_errors = True)
		shutil.copytree (self.bundle_skeleton_dir, self.bundle_app_dir)
		if not os.path.exists (self.bundle_contents_dir): os.makedirs (self.bundle_contents_dir)
		if not os.path.exists (self.bundle_res_dir): os.makedirs (self.bundle_res_dir)
		if not os.path.exists (self.bundle_macos_dir): os.makedirs (self.bundle_macos_dir)

		# Generate the PkgInfo
		pkginfo_path = os.path.join (self.bundle_contents_dir, 'PkgInfo')
		if not os.path.exists (pkginfo_path) and not plist == None:
			fp = open (pkginfo_path, 'w')
			fp.write (plist['CFBundlePackageType'])
			fp.write (plist['CFBundleSignature'])
			fp.close ()

		# Run solitary against the installation to collect files
		files = ''
		for file in self.bundle_from_build:
			files = files + ' "%s"' % os.path.join (self.prefix, file)

		run_shell ('mono --debug ../../solitary/Solitary.exe '
			'--mono-prefix="%s" --root="%s" --out="%s" %s' % \
			(self.prefix, self.prefix, self.bundle_res_dir, files))
		self.configure_gtk ()
		self.configure_gdk_pixbuf ()

	def configure_gtk (self):
		paths = [
			os.path.join ('etc', 'gtk-2.0', 'gtk.immodules'),
			os.path.join ('etc', 'gtk-2.0', 'im-multipress.conf'),
			os.path.join ('etc', 'pango', 'pango.modules')
		]

		for path in paths:
			bundle_path = os.path.join (self.bundle_res_dir, path) + '.in'
			path = os.path.join (self.prefix, path)

			if not os.path.isfile (path):
				continue

			try:
				os.makedirs (os.path.dirname (bundle_path))
			except:
				pass

			ifp = open (path)
			ofp = open (bundle_path, 'w')
			for line in ifp:
				if line.startswith ('#'):
					continue
				ofp.write (line.replace (self.prefix, '${APP_RESOURCES}'))
			ifp.close ()
			ofp.close ()

			if os.path.basename (path) == 'pango.modules':
				fp = open (os.path.join (os.path.dirname (bundle_path), 'pangorc'), 'w')
				fp.write ('[Pango]\n')
				fp.write ('ModuleFiles=./pango.modules\n')
				fp.close ()

	def configure_gdk_pixbuf (self):
		path = os.path.join (self.bundle_res_dir, 'etc', 'gtk-2.0', 'gdk-pixbuf.loaders.in')
		run_shell ('gdk-pixbuf-query-loaders 2>/dev/null | ' + \
			'sed \'s,%s,\\${APP_RESOURCES},g\' 1> "%s"' % (self.prefix, path))

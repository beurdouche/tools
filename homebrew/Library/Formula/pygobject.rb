require 'formula'

class Pygobject < Formula
  url 'http://ftp.gnome.org/pub/GNOME/sources/pygobject/2.28/pygobject-2.28.6.tar.bz2'
  homepage 'http://live.gnome.org/PyGObject'
  md5 'a43d783228dd32899e6908352b8308f3'

  depends_on 'pkg-config' => :build
  depends_on 'gobject-introspection'
  depends_on 'gtk+'

  # https://bugzilla.gnome.org/show_bug.cgi?id=668522
  def patches
    "http://git.gnome.org/browse/pygobject/patch/gio/gio-types.defs?id=42d01f060c5d764baa881d13c103d68897163a49"
  end

  def options
    [["--universal", "Builds a universal binary"]]
  end

  def install
    ENV.universal_binary if ARGV.build_universal?
    system "./configure", "--disable-dependency-tracking",
                          "--prefix=#{prefix}",
                          "--disable-introspection"
    system "make install"
  end
end

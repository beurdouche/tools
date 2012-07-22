require 'formula'

class FrameworkPython < Requirement
  def message; <<-EOS.undent
    Python needs to be built as a framework.
    EOS
  end
  def satisfied?
    q = `python -c "import distutils.sysconfig as c; print(c.get_config_var('PYTHONFRAMEWORK'))"`
    not q.chomp.empty?
  end
  def fatal?; true; end
end

class Wxmac < Formula
  homepage 'http://www.wxwidgets.org'
  url 'http://sourceforge.net/projects/wxpython/files/wxPython/2.9.3.1/wxPython-src-2.9.3.1.tar.bz2'
  sha1 '0202f64e1e99fb69d22d7be0d38cf7dcf3d80d79'

  def options
    [['--no-python', 'Do not build Python bindings']]
  end

  depends_on FrameworkPython.new unless ARGV.include? "--no-python"

  def patches
    # webkit and clang 3.x needs fix for wx(Python) 2.9.3.1: http://trac.wxwidgets.org/ticket/13565
    if MacOS.clang_version.to_f >= 3.0
      { :p0 => "http://trac.wxwidgets.org/raw-attachment/ticket/13565/ClangCompat.diff" }
    end
  end

  def install_wx_python
    args = [
      # Reference our wx-config
      "WX_CONFIG=#{bin}/wx-config",
      # At this time Wxmac is installed Unicode only
      "UNICODE=1",
      # And thus we have no need for multiversion support
      "INSTALL_MULTIVERSION=0",
      # OpenGL and stuff
      "BUILD_GLCANVAS=1",
      "BUILD_GIZMOS=1",
      "BUILD_STC=1"
    ]
    cd "wxPython" do
      ENV.append_to_cflags '-arch x86_64' if MacOS.prefer_64_bit?

      system "python", "setup.py",
                       "build_ext",
                       "WXPORT=osx_cocoa",
                       *args
      system "python", "setup.py",
                       "install",
                       "--prefix=#{prefix}",
                       "WXPORT=osx_cocoa",
                       *args
    end
  end

  def install
    args = [
      "--disable-debug",
      "--prefix=#{prefix}",
      "--enable-unicode",
      "--enable-std_string",
      "--enable-display",
      "--with-opengl",
      "--with-osx_cocoa",
      "--with-libjpeg",
      "--with-libtiff",
      "--with-libpng",
      "--with-zlib",
      "--enable-dnd",
      "--enable-clipboard",
      "--enable-webkit",
      "--enable-svg",
      "--with-expat",
      "--with-macosx-version-min=#{MacOS.version}" # need to set this, to avoid configure defaulting to 10.5
    ]

    system "./configure", *args
    system "make install"

    unless ARGV.include? "--no-python"
      ENV['WXWIN'] = Dir.getwd
      # We have already downloaded wxPython in a bundle with wxWidgets
      install_wx_python
    end
  end

  def caveats
    s = ''
    unless ARGV.include? '--no-python'
      q = `python -c "import distutils.sysconfig as c; print(c.get_config_var('PYTHONFRAMEWORK'))"`
      if q.chomp.empty?
        s += <<-EOS.undent
          Python bindings require that Python be built as a Framework.

        EOS
      end
    end

    return s
  end
end

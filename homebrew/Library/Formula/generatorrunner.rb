require 'formula'

class Generatorrunner < Formula
  homepage 'http://www.pyside.org/docs/generatorrunner'
  url 'http://pyside.org/files/generatorrunner-0.6.16.tar.bz2'
  md5 'c7011b8ee08e228779a769b7cfa90f5f'

  depends_on 'cmake' => :build

  depends_on 'apiextractor'

  def install
    system "cmake", ".",
                    "-DCMAKE_INSTALL_NAME_DIR=#{HOMEBREW_PREFIX}/lib",
                    "-DCMAKE_BUILD_WITH_INSTALL_RPATH=ON",
                    *std_cmake_args
    system "make install"
  end
end

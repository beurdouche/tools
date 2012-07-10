require 'testing_env'

def file pn
  `/usr/bin/file -h '#{pn}'`.chomp
end

class MachOPathnameTests < Test::Unit::TestCase
  def test_fat_dylib
    pn = Pathname.new("#{TEST_FOLDER}/mach/fat.dylib")
    assert pn.universal?
    assert !pn.i386?
    assert !pn.x86_64?
    assert !pn.ppc7400?
    assert !pn.ppc64?
    assert pn.dylib?
    assert !pn.mach_o_executable?
    assert !pn.text_executable?
    assert pn.arch == :universal
    assert_match /Mach-O (64-bit )?dynamically linked shared library/, file(pn)
  end

  def test_i386_dylib
    pn = Pathname.new("#{TEST_FOLDER}/mach/i386.dylib")
    assert !pn.universal?
    assert pn.i386?
    assert !pn.x86_64?
    assert !pn.ppc7400?
    assert !pn.ppc64?
    assert pn.dylib?
    assert !pn.mach_o_executable?
    assert !pn.text_executable?
    assert !pn.mach_o_bundle?
    assert_match /Mach-O dynamically linked shared library/, file(pn)
  end

  def test_x86_64_dylib
    pn = Pathname.new("#{TEST_FOLDER}/mach/x86_64.dylib")
    assert !pn.universal?
    assert !pn.i386?
    assert pn.x86_64?
    assert !pn.ppc7400?
    assert !pn.ppc64?
    assert pn.dylib?
    assert !pn.mach_o_executable?
    assert !pn.text_executable?
    assert !pn.mach_o_bundle?
    assert_match /Mach-O 64-bit dynamically linked shared library/, file(pn)
  end

  def test_mach_o_executable
    pn = Pathname.new("#{TEST_FOLDER}/mach/a.out")
    assert pn.universal?
    assert !pn.i386?
    assert !pn.x86_64?
    assert !pn.ppc7400?
    assert !pn.ppc64?
    assert !pn.dylib?
    assert pn.mach_o_executable?
    assert !pn.text_executable?
    assert !pn.mach_o_bundle?
    assert_match /Mach-O (64-bit )?executable/, file(pn)
  end

  def test_fat_bundle
    pn = Pathname.new("#{TEST_FOLDER}/mach/fat.bundle")
    assert pn.universal?
    assert !pn.i386?
    assert !pn.x86_64?
    assert !pn.ppc7400?
    assert !pn.ppc64?
    assert !pn.dylib?
    assert !pn.mach_o_executable?
    assert !pn.text_executable?
    assert pn.mach_o_bundle?
    assert_match /Mach-O (64-bit )?bundle/, file(pn)
  end

  def test_i386_bundle
    pn = Pathname.new("#{TEST_FOLDER}/mach/i386.bundle")
    assert !pn.universal?
    assert pn.i386?
    assert !pn.x86_64?
    assert !pn.ppc7400?
    assert !pn.ppc64?
    assert !pn.dylib?
    assert !pn.mach_o_executable?
    assert !pn.text_executable?
    assert pn.mach_o_bundle?
    assert_match /Mach-O bundle/, file(pn)
  end

  def test_x86_64_bundle
    pn = Pathname.new("#{TEST_FOLDER}/mach/x86_64.bundle")
    assert !pn.universal?
    assert !pn.i386?
    assert pn.x86_64?
    assert !pn.ppc7400?
    assert !pn.ppc64?
    assert !pn.dylib?
    assert !pn.mach_o_executable?
    assert !pn.text_executable?
    assert pn.mach_o_bundle?
    assert_match /Mach-O 64-bit bundle/, file(pn)
  end

  def test_non_mach_o
    pn = Pathname.new("#{TEST_FOLDER}/tarballs/testball-0.1.tbz")
    assert !pn.universal?
    assert !pn.i386?
    assert !pn.x86_64?
    assert !pn.ppc7400?
    assert !pn.ppc64?
    assert !pn.dylib?
    assert !pn.mach_o_executable?
    assert !pn.text_executable?
    assert !pn.mach_o_bundle?
    assert pn.arch == :dunno
    assert_no_match /Mach-O (64-bit )?dynamically linked shared library/, file(pn)
    assert_no_match /Mach-O [^ ]* ?executable/, file(pn)
  end

  def test_architecture_list_extension
    archs = [:i386, :x86_64, :ppc7400, :ppc64]
    archs.extend(ArchitectureListExtension)
    assert archs.universal?
    archs.remove_ppc!
    assert_equal 2, archs.length
    assert_match /-arch i386/, archs.as_arch_flags
    assert_match /-arch x86_64/, archs.as_arch_flags

    pn = Pathname.new("#{TEST_FOLDER}/mach/fat.dylib")
    assert pn.archs.universal?
    assert_match /-arch i386/, pn.archs.as_arch_flags
    assert_match /-arch x86_64/, pn.archs.as_arch_flags
  end
end

class TextExecutableTests < Test::Unit::TestCase
  def test_simple_shebang
    pn = Pathname.new('foo')
    pn.write '#!/bin/sh'
    assert !pn.universal?
    assert !pn.i386?
    assert !pn.x86_64?
    assert !pn.ppc7400?
    assert !pn.ppc64?
    assert !pn.dylib?
    assert !pn.mach_o_executable?
    assert pn.text_executable?
    assert_equal [], pn.archs
    assert pn.arch == :dunno
    assert_match /text executable/, file(pn)
  end

  def test_shebang_with_options
    pn = Pathname.new('bar')
    pn.write '#! /usr/bin/perl -w'
    assert !pn.universal?
    assert !pn.i386?
    assert !pn.x86_64?
    assert !pn.ppc7400?
    assert !pn.ppc64?
    assert !pn.dylib?
    assert !pn.mach_o_executable?
    assert pn.text_executable?
    assert_equal [], pn.archs
    assert pn.arch == :dunno
    assert_match /text executable/, file(pn)
  end

  def test_malformed_shebang
    pn = Pathname.new('baz')
    pn.write ' #!'
    assert !pn.universal?
    assert !pn.i386?
    assert !pn.x86_64?
    assert !pn.ppc7400?
    assert !pn.ppc64?
    assert !pn.dylib?
    assert !pn.mach_o_executable?
    assert !pn.text_executable?
    assert_equal [], pn.archs
    assert pn.arch == :dunno
    assert_no_match /text executable/, file(pn)
  end
end

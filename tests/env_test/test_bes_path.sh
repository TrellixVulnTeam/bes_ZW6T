#!/bin/bash

source $_BES_DEV_ROOT/env/bes_path.sh
source $_BES_DEV_ROOT/env/bes_testing.sh

function test_bes_path_dedup()
{
  bes_assert "[ $(bes_path_dedup /bin:/foo:/bin) = /bin:/foo ]"
  bes_assert "[ $(bes_path_dedup /bin:/bin:/bin) = /bin ]"
  bes_assert "[ $(bes_path_dedup /bin::/bin:/bin) = /bin: ]"
  bes_assert "[ $(bes_path_dedup /bin::/bin:/bin:::) = /bin: ]"
  bes_assert "[ $(bes_path_dedup \"\") = \"\" ]"
  bes_assert "[ $(bes_path_dedup /bin:/foo/bin:/bin) = /bin:/foo/bin ]"
}

function test_bes_path_sanitize()
{
  bes_assert "[ $(bes_path_sanitize /bin:/foo:/bin) = /bin:/foo ]"
  bes_assert "[ $(bes_path_sanitize /bin:/bin:/bin) = /bin ]"
  bes_assert "[ $(bes_path_sanitize :/bin) = /bin ]"
  bes_assert "[ $(bes_path_sanitize /bin::/bin:/bin:::) = /bin ]"
  bes_assert "[ $(bes_path_sanitize \"\") = \"\" ]"
  bes_assert "[ $(bes_path_sanitize :a::::b:) = a:b ]"
  bes_assert "[ $(bes_path_sanitize a:b:c:a:b:c) = a:b:c ]"
}

function test_bes_path_append()
{
  bes_assert "[ $(bes_path_append /bin /foo/bin) = /bin:/foo/bin ]"
  bes_assert "[ $(bes_path_append /bin:/foo/bin /foo/bin) = /bin:/foo/bin ]"
  bes_assert "[ $(bes_path_append /bin:/foo/bin /foo/bin /bar/bin) = /bin:/foo/bin:/bar/bin ]"
  bes_assert "[ $(bes_path_append /bin:/foo/bin /bin) = /foo/bin:/bin ]"
  bes_assert "[ $(bes_path_append foo bar) = foo:bar ]"
  bes_assert "[ $(bes_path_append foo bar bar foo) = bar:foo ]"
}

function test_bes_path_prepend()
{
  bes_assert "[ $(bes_path_prepend /bin /foo/bin) = /foo/bin:/bin ]"
  bes_assert "[ $(bes_path_prepend /foo/bin:/bin /foo/bin) = /foo/bin:/bin ]"
  bes_assert "[ $(bes_path_prepend /foo/bin:/bin /bin) = /bin:/foo/bin ]"
}

function test_bes_path_remove()
{
  bes_assert "[ $(bes_path_remove /bin:/foo/bin /foo/bin) = /bin ]"
  bes_assert "[ $(bes_path_remove /bin:/foo/bin foo/bin) = /bin:/foo/bin ]"
  bes_assert "[ $(bes_path_remove foo:bar bar) = foo ]"
  bes_assert "[ $(bes_path_remove foo:bar bar foo) = ]"
}

bes_testing_run_unit_tests


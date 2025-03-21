package("duckdb")
    set_homepage("http://duckdb.org/")
    set_description("DuckDB is an in-process SQL OLAP Database Management System")
    set_license("MIT")

    on_source("windows", "macosx", "linux", function(package)
        local precompiled = false
        if package:is_plat("windows") then
            if package:is_arch("x64", "x86_64") then
                precompiled = true
                package:add("urls", "https://github.com/duckdb/duckdb/releases/download/$(version)/libduckdb-windows-amd64.zip")
                package:add("versions", "v1.2.1", "c977230a701d6b274fe63166868c8e2bc4ec23cf42c44f08f22bdcd8ed4a8e31")
            elseif package:is_arch("arm64") then
                precompiled = true
                package:add("urls", "https://github.com/duckdb/duckdb/releases/download/$(version)/libduckdb-windows-arm64.zip")
                package:add("versions", "v1.2.1", "de02a9e3e64b41ea7844aa04ad7e72519ca131327e739cd344a6ba476fb31c0f")
            end
        elseif package:is_plat("linux") then
            if package:config("shared") then
                if package:is_arch("x64", "x86_64") then
                    precompiled = true
                    package:add("urls", "https://github.com/duckdb/duckdb/releases/download/$(version)/libduckdb-linux-amd64.zip")
                    package:add("versions", "v1.2.1", "8dda081c84ef1da07f19f953ca95e1c6db9b6851e357444a751ad45be8a14d36")
                elseif package:is_arch("arm64") then
                    precompiled = true
                    package:add("urls", "https://github.com/duckdb/duckdb/releases/download/$(version)/libduckdb-linux-arm64.zip")
                    package:add("versions", "v1.2.1", "b1fc7c892414fdc286a7d99cd374634deb586e0fcccc87cb84a2b52272f93bfd")
                end
            elseif package:config("static") then
                if package:is_arch("x64", "x86_64") then
                    precompiled = true
                    package:add("urls", "https://github.com/duckdb/duckdb/releases/download/$(version)/static-lib-linux-amd64.zip")
                    package:add("versions", "v1.2.1", "be614d4b36621bce1da8ad545fd0fc46c6094232ce5fe8a135bf69455110bfa1")
                elseif package:is_arch("arm64") then
                    precompiled = true
                    package:add("urls", "https://github.com/duckdb/duckdb/releases/download/$(version)/static-lib-linux-arm64.zip")
                    package:add("versions", "v1.2.1", "ab5d43238972cfb7ae1852f8890103a056d09ff5ce60623a8515729c49e1d6c0")
                end
            end
        elseif package:is_plat("macosx") then
            if package:config("shared") then
                precompiled = true
                package:add("urls", "https://github.com/duckdb/duckdb/releases/download/$(version)/libduckdb-osx-universal.zip")
                package:add("versions", "v1.2.1", "5045ad331e6e738ba4d2299e8726f200be82f6da961f208973f48df7a4532ce1")
            elseif package:config("static") then
                if package:is_arch("x64", "x86_64") then
                    precompiled = true
                    package:add("urls", "https://github.com/duckdb/duckdb/releases/download/$(version)/static-lib-osx-amd64.zip")
                    package:add("versions", "v1.2.1", "be614d4b36621bce1da8ad545fd0fc46c6094232ce5fe8a135bf69455110bfa1")
                elseif package:is_arch("arm64") then
                    precompiled = true
                    package:add("urls", "https://github.com/duckdb/duckdb/releases/download/$(version)/static-lib-osx-arm64.zip")
                    package:add("versions", "v1.2.1", "ab5d43238972cfb7ae1852f8890103a056d09ff5ce60623a8515729c49e1d6c0")
                end
            end
        end

        if not precompiled then
             package:add("urls", "https://github.com/duckdb/duckdb/archive/refs/tags/$(version).zip",
                                 "https://github.com/duckdb/duckdb.git")
            package:add("versions", "v1.2.1", "8d17ce47dc16c8e3dde41a09916eb63034cb19dd2c6bd71b90372261a43b8b71")
            package:add("versions", "v1.1.3", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
            package:add("versions", "v1.1.2", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
            package:add("versions", "v1.1.1", "cedf308dca577d2c5e44b34948529cb0ce932da27cd54ed611c926d49473c732")
            package:add("versions", "v1.0.0", "6b8b410745dd763058af727ae45a37b34c22418c866dd3df94cbb3a0bc622992")
            package:add("versions", "v0.10.3", "9e7372f2b23cada55200e07da407f2c3c261f9aaeb364b8e0908f0682bf3a895")
            package:add("versions", "v0.10.2", "309af78e1ad8326841454bcd7203bb04ee8ca8279de3f6357a8a3e4c94842989")
            package:add("versions", "v0.10.1", "1da8dbe3c984f82ff35cb40982e9605fd4670681e6f9ee44931facc41c782c58")
            package:add("versions", "v0.10.0", "9162e6ef0fc53cdfe4b9ded5c4c3260a4cd8e2d812a953d2d8bd0b9afdb5e09c")
        end
        package:data_set("precompiled", precompiled)
    end)

    on_load("windows", "macosx", "linux", function (package)
        if not package:data("precompiled") then
            package:add("deps", "cmake")
        end
    end)

    on_install("windows", "macosx", "linux", function (package)
        if package:data("precompiled") then
            os.trycp("*.dll", package:installdir("lib"))
            os.trycp("*.lib", package:installdir("lib"))
            os.trycp("*.a", package:installdir("lib"))
            os.trycp("*.dylib", package:installdir("lib"))
            os.trycp("*.so", package:installdir("lib"))
            os.trycp("*.h", package:installdir("include"))
            os.trycp("*.hpp", package:installdir("include"))
            return
        end

        local configs = {}
        table.insert(configs, "-DCMAKE_BUILD_TYPE=" .. (package:debug() and "Debug" or "Release"))
        table.insert(configs, "-DBUILD_SHARED_LIBS=" .. (package:config("shared") and "ON" or "OFF"))
        table.insert(configs, "-DEXTENSION_STATIC_BUILD=" .. (package:config("shared") and "ON" or "OFF"))
        table.insert(configs, "-DBUILD_UNITTESTS=0")
        table.insert(configs, "-DBUILD_SHELL=0")

        import("package.tools.cmake").install(package, configs)
    end)

    on_test("windows", "macosx", "linux", function (package)
        assert(package:check_cxxsnippets({test = [[
            #include "duckdb.hpp"
            using namespace duckdb;

            void test() {
                DuckDB db(nullptr);
                Connection con(db);
            }
        ]]}, {configs = {languages = "c++17"}}))
    end)
package_end()

add_rules("mode.debug", "mode.release")
add_repositories("Concerto-xrepo https://github.com/ConcertoEngine/xmake-repo.git main")

add_requires("vulkan-headers", "concerto-core", "mimalloc", "duckdb", "vulkan-utility-libraries")

-- VK_ADD_IMPLICIT_LAYER_PATH=C:/Users/Arthur/Documents/Git/GraphicsEngineInspector/VK_LAYER_gei.json
-- VK_LAYERS_ALLOW_ENV_VAR=1
-- VK_INSTANCE_LAYERS=VK_LAYER_AV_gei
-- VK_LOADER_LAYERS_ENABLE=VK_LAYER_AV_gei
-- ENABLE_GEI_LAYER=1
-- VK_LOADER_DEBUG=all

target("vmi-layer")
    -- before_build(function(target)
    --     import("devel.git")
    --     local clone_path = path.join(target:targetdir(),"/Vulkan-Docs")

    --     if not os.exists(clone_path) then
    --         git.clone("git@github.com:KhronosGroup/Vulkan-Docs.git", {outputdir = clone_path})
    --     else
    --        -- git.pull({repodir=clone_path})
    --     end
    --     local out_file = path.join(target:autogendir(), "VMI")
    --     --python.exe ./scripts/genvk.py -registry ./xml/vk.xml -o ../gen/include/vulkan vulkan_core.h
    --     os.vrun("python.exe ./" .. path.join(clone_path, "scripts/genvk.py") .. " -registry ./" .. path.join(clone_path, "xml/vk.xml") .. " -o ./" .. out_file .. " vulkan_core.h")

    --     target:add("headerfiles", path.join(target:autogendir(), out_file))
    --     target:add("includedirs", path.join(target:autogendir(), out_file), {public = true})
    -- end)
    set_kind("shared")
    set_languages("cxx20")
    add_files("Src/VMI/**.cpp")
    add_includedirs("Include")
    add_headerfiles("Include/VMI/*.hpp", "Include/VMI/*.inl", "Include/vulkan/*.c", "Include/vulkan/*.h")
    add_packages("vulkan-headers", "concerto-core", "mimalloc", "duckdb", "vulkan-utility-libraries")
    add_defines("VK_NO_PROTOTYPES")
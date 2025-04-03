set_policy("package.sync_requires_to_deps", true)
add_rules("mode.debug", "mode.release")
add_repositories("Concerto-xrepo https://github.com/ConcertoEngine/xmake-repo.git main")

add_requires("concerto-core", {configs = {shared = false}})
add_requires("vulkan-headers", "mimalloc", "vulkan-utility-libraries", "nlohmann_json", "python 3.x")

-- VK_ADD_IMPLICIT_LAYER_PATH=D:/Repositories/Vulkan/VMILayer/vmi-layer/VK_LAYER_vmi.json
-- VK_LAYERS_ALLOW_ENV_VAR=1
-- VK_INSTANCE_LAYERS=VK_LAYER_AV_vmi
-- VK_LOADER_LAYERS_ENABLE=VK_LAYER_AV_vmi
-- ENABLE_VMI_LAYER=1
-- VK_LOADER_DEBUG=all

target("vmi-layer")
    set_kind("shared")
    set_languages("cxx20")
    add_files("Src/VMI/**.cpp")
    add_includedirs("Include")
    add_headerfiles("Include/VMI/*.hpp", "Include/VMI/*.inl")
    add_packages("vulkan-headers", "concerto-core", "mimalloc", "vulkan-utility-libraries", "nlohmann_json", "cppzmq")
    add_defines("VK_NO_PROTOTYPES")

    on_config(function(target)
        local out_folder = target:autogendir()
        local out_file = path.join(out_folder, "VMI", "Bindings.hpp")
        local header_file = target:autogendir() .. "/(VMI/*.hpp)"
        os.execv("python.exe", { "../generate_bindings.py", "cpp", out_file, "../schema.json" })

        target:add("headerfiles", header_file)
        target:add("includedirs", out_folder, {public = true})
    end)

    after_build(function(target)
        local lib_path = path.absolute(target:targetfile())
        local json_content = string.format([[
        {
            "file_format_version" : "1.2.1",
            "layer" : {
                "name": "VK_LAYER_AV_vmi",
                "type": "GLOBAL",
                "library_path": %q,
                "api_version": "1.0.0",
                "implementation_version": "1.3",
                "description": "Vulkan memory inspector layer",
                "enable_environment": {
                    "ENABLE_VMI_LAYER": "1"
                },
                "disable_environment": {
                    "DISABLE_VMI_LAYER": ""
                }
            }
        }
        ]], lib_path)

        io.writefile("VK_LAYER_vmi.json", json_content)
    end)
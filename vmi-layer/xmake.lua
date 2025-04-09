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
    add_includedirs("Include", ".")
    add_headerfiles("Include/VMI/*.hpp", "Include/VMI/*.inl")
    add_packages("vulkan-headers", "concerto-core", "mimalloc", "vulkan-utility-libraries", "nlohmann_json", "cppzmq")
    add_defines("VK_NO_PROTOTYPES")

    on_config(function(target)
        import('net.http')

        local out_folder = target:autogendir()
        local out_file = path.join(out_folder, "VMI", "Bindings.hpp")

        -- Bindings generation
        local header_file = target:autogendir() .. "/(VMI/*.hpp)"
        target:add("headerfiles", header_file)
        os.execv("python.exe", { "../generate_bindings.py", "cpp", out_file, "../schema.json" })
        target:add("includedirs", out_folder, {public = true})

        -- Vulkan Struct to JSON generation
        local out_json_file = path.join(out_folder, "VMI", "VulkanStructToJson.cpp")
        local out_json_hpp_file = path.join(out_folder, "VMI", "VulkanStructToJson.hpp")
        target:add("files", out_json_file, {public = true})
        target:add("headerfiles", out_json_hpp_file)

        -- Vulkan Commands generation
        http.download('https://raw.githubusercontent.com/KhronosGroup/Vulkan-Docs/main/xml/vk.xml', path.join(out_folder, "vk.xml"))
        http.download('https://raw.githubusercontent.com/KhronosGroup/Vulkan-Docs/main/xml/video.xml', path.join(out_folder, "video.xml"))
        local out_cpp_file = path.join(out_folder, "VMI", "VulkanCommands.cpp")
        local out_hpp_file = path.join(out_folder, "VMI", "VulkanCommands.hpp")
        target:add("files", out_cpp_file, {public = true})
        target:add("headerfiles", out_hpp_file)

        os.execv("python.exe", { "./gen_commands.py",  path.join(out_folder, "vk.xml"),  path.join(out_folder, "video.xml"), path.join(out_folder, "VMI")})
        --python.exe "./gen_commands.py" "build/.gens/vmi-layer/windows/x64/debug/vk.xml" "build/.gens/vmi-layer/windows/x64/debug/VMI"

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
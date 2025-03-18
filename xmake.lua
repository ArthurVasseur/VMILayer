add_rules("mode.debug", "mode.release")
add_repositories("Concerto-xrepo https://github.com/ConcertoEngine/xmake-repo.git main")

add_requires("vulkan-headers", "concerto-core", "mimalloc")

-- VK_ADD_IMPLICIT_LAYER_PATH=C:/Users/Arthur/Documents/Git/GraphicsEngineInspector/VK_LAYER_gei.json
-- VK_LAYERS_ALLOW_ENV_VAR=1
-- VK_INSTANCE_LAYERS=VK_LAYER_AV_gei
-- VK_LOADER_LAYERS_ENABLE=VK_LAYER_AV_gei
-- ENABLE_GEI_LAYER=1
-- VK_LOADER_DEBUG=all

target("vmi-layer")
    set_kind("shared")
    set_languages("cxx20")
    add_files("Src/VMI/**.cpp")
    add_includedirs("Include")
    add_headerfiles("Include/VMI/*.hpp", "Include/VMI/*.inl", "Include/vulkan/*.c", "Include/vulkan/*.h")
    add_packages("vulkan-headers", "concerto-core", "mimalloc")
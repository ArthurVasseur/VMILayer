//
// Created by arthur on 01/03/2025.
//

#ifndef GEI_GRAPHICSENGINEINTERCEPTOR_INL
#define GEI_GRAPHICSENGINEINTERCEPTOR_INL

#include "Viewer.hpp"
#include "VMI/VulkanMemoryInspector.hpp"

inline VulkanMemoryInspector& VulkanMemoryInspector::GetInstance()
{
	return instance;
}

inline void VulkanMemoryInspector::AddInstanceDispatchTable(void* instance, VkuInstanceDispatchTable table)
{
	std::lock_guard _(instanceDispatchTablesMutex);
	instanceDispatchTables.emplace(instance, table);
}

inline void VulkanMemoryInspector::AddDeviceDispatchTable(void* device, VkuDeviceDispatchTable table)
{
	std::lock_guard _(deviceDispatchTablesMutex);
	deviceDispatchTables.emplace(device, table);
}

inline const VkuInstanceDispatchTable* VulkanMemoryInspector::GetInstanceDispatchTable(void* instance)
{
	std::lock_guard _(instanceDispatchTablesMutex);

	auto it = instanceDispatchTables.find(instance);
	if (it == instanceDispatchTables.end())
		return nullptr;
	return &it->second;
}

inline const VkuDeviceDispatchTable* VulkanMemoryInspector::GetDeviceDispatchTable(void* device)
{
	std::lock_guard _(deviceDispatchTablesMutex);

	auto it = deviceDispatchTables.find(device);
	if (it == deviceDispatchTables.end())
		return nullptr;
	return &it->second;
}

inline vmi::Viewer* VulkanMemoryInspector::GetViewer(void* device)
{
	auto it = _viewers.find(device);
	if (it == _viewers.end())
		return nullptr;
	return it->second.get();
}

inline VkAllocationCallbacks VulkanMemoryInspector::GetAllocationCallbacks() const
{
	return _allocationCallbacks;
}

inline duckdb::Connection& VulkanMemoryInspector::GetDataBaseConnection()
{
	return dbConnection;
}

inline VkResult VulkanMemoryInspector::CreateViewer(void* pDevice)
{
	duckdb::Connection connection(db);
	
	auto viewer = std::make_unique<vmi::Viewer>(std::move(connection));
	auto result = viewer->Create();
	if (result.IsError())
	{
		SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, "Error", result.GetError().c_str(), nullptr);
		return VK_ERROR_INITIALIZATION_FAILED;
	}
	_viewers.emplace(pDevice, std::move(viewer));
	return VK_SUCCESS;
}


#endif //GEI_GRAPHICSENGINEINTERCEPTOR_INL

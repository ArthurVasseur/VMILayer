//
// Created by arthur on 01/03/2025.
//

#ifndef GEI_GRAPHICSENGINEINTERCEPTOR_INL
#define GEI_GRAPHICSENGINEINTERCEPTOR_INL

#include "VMI/VulkanMemoryInspector.hpp"

inline std::shared_ptr<VulkanMemoryInspector> VulkanMemoryInspector::GetInstance()
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

inline VkAllocationCallbacks VulkanMemoryInspector::GetAllocationCallbacks() const
{
	return _allocationCallbacks;
}

inline cct::Int32 VulkanMemoryInspector::GetFrameIndex() const
{
	return _frameIndex;
}

inline void VulkanMemoryInspector::NextFrame()
{
	++_frameIndex;
}

inline void VulkanMemoryInspector::Send(std::span<cct::Byte> memoryBlock)
{
	if (!_socket)
	{
		CCT_ASSERT_FALSE("Invalid socket pointer");
		return;
	}
	_socket->Send(memoryBlock.data(), memoryBlock.size());
}

inline void VulkanMemoryInspector::CreateInstance()
{
	instance = std::make_shared<VulkanMemoryInspector>();
}

inline void VulkanMemoryInspector::DestroyInstance()
{
	instance = nullptr;
}

#endif //GEI_GRAPHICSENGINEINTERCEPTOR_INL

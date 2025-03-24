//
// Created by arthur on 01/03/2025.
//

#ifndef VMI_VULKANMEMORYINTERCEPTOR_HPP
#define VMI_VULKANMEMORYINTERCEPTOR_HPP

#include <mutex>
#include <unordered_map>

#include <duckdb.hpp>

#include "VMI/VulkanFunctions.hpp"

namespace vmi
{
	class Viewer;
}

struct LowerAllocation
{
	const VkAllocationCallbacks* allocationCallbacks;
};

class VulkanMemoryInspector
{
public:
	VulkanMemoryInspector();

	static VulkanMemoryInspector& GetInstance();

	void AddInstanceDispatchTable(void* instance, VkuInstanceDispatchTable table);
	void AddDeviceDispatchTable(void* device, VkuDeviceDispatchTable table);
	const VkuInstanceDispatchTable* GetInstanceDispatchTable(void* instance);
	const VkuDeviceDispatchTable* GetDeviceDispatchTable(void* device);
	vmi::Viewer* GetViewer(void* device);
	VkAllocationCallbacks GetAllocationCallbacks() const;
	inline duckdb::Connection& GetDataBaseConnection();
	VkResult CreateViewer(void* pDevice);

private:
	static void* AllocationFunction(void* pUserData, size_t size, size_t alignment, VkSystemAllocationScope allocationScope);
	static void* ReallocationFunction(void* pUserData, void* pOriginal, size_t size, size_t alignment, VkSystemAllocationScope allocationScope);
	static void FreeFunction(void* pUserData, void* pMemory);
	static void InternalAllocationNotification(void* pUserData, size_t size, VkInternalAllocationType allocationType, VkSystemAllocationScope allocationScope);
	static void InternalFreeNotification(void* pUserData, size_t size, VkInternalAllocationType allocationType, VkSystemAllocationScope allocationScope);

	static VulkanMemoryInspector instance;

	std::mutex instanceDispatchTablesMutex;
	std::unordered_map<void*, VkuInstanceDispatchTable> instanceDispatchTables;

	std::mutex deviceDispatchTablesMutex;
	std::unordered_map<void*, VkuDeviceDispatchTable> deviceDispatchTables;

	std::unordered_map<void* /*device*/, std::unique_ptr<vmi::Viewer>> _viewers;
	VkAllocationCallbacks _allocationCallbacks;
	duckdb::DuckDB db;
	duckdb::Connection dbConnection;
};

#include "VMI/VulkanMemoryInspector.inl"

#endif //VMI_VULKANMEMORYINTERCEPTOR_HPP
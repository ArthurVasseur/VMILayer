//
// Created by arthur on 01/03/2025.
//

#ifndef VMI_VULKANMEMORYINTERCEPTOR_HPP
#define VMI_VULKANMEMORYINTERCEPTOR_HPP

#include <mutex>
#include <span>
#include <unordered_map>
#include <Concerto/Core/Network/Socket.hpp>
#include "VMI/VulkanFunctions.hpp"
#define VMI_GET_PROC_ADDR(func) if(!strcmp(pName, #func)) return (PFN_vkVoidFunction)&(func)
struct LowerAllocation
{
	const VkAllocationCallbacks* allocationCallbacks;
};

class VulkanMemoryInspector
{
public:
	VulkanMemoryInspector();
	~VulkanMemoryInspector();
	static std::shared_ptr<VulkanMemoryInspector> GetInstance();
	static void CreateInstance();
	static void DestroyInstance();

	void AddInstanceDispatchTable(void* instance, VkuInstanceDispatchTable table);
	void AddDeviceDispatchTable(void* device, VkuDeviceDispatchTable table);
	const VkuInstanceDispatchTable* GetInstanceDispatchTable(void* instance);
	const VkuDeviceDispatchTable* GetDeviceDispatchTable(void* device);
	VkAllocationCallbacks GetAllocationCallbacks() const;
	cct::Int32 GetFrameIndex() const;
	void NextFrame();
	void Send(std::span<cct::Byte> memoryBlock);

private:
	static void* AllocationFunction(void* pUserData, size_t size, size_t alignment, VkSystemAllocationScope allocationScope);
	static void* ReallocationFunction(void* pUserData, void* pOriginal, size_t size, size_t alignment, VkSystemAllocationScope allocationScope);
	static void FreeFunction(void* pUserData, void* pMemory);
	static void InternalAllocationNotification(void* pUserData, size_t size, VkInternalAllocationType allocationType, VkSystemAllocationScope allocationScope);
	static void InternalFreeNotification(void* pUserData, size_t size, VkInternalAllocationType allocationType, VkSystemAllocationScope allocationScope);

	static std::shared_ptr<VulkanMemoryInspector> instance;

	std::mutex instanceDispatchTablesMutex;
	std::unordered_map<void*, VkuInstanceDispatchTable> instanceDispatchTables;

	std::mutex deviceDispatchTablesMutex;
	std::unordered_map<void*, VkuDeviceDispatchTable> deviceDispatchTables;


	VkAllocationCallbacks _allocationCallbacks;
	cct::Int32 _frameIndex;

	std::unique_ptr<cct::net::Socket> _socket;
};

#include "VMI/VulkanMemoryInspector.inl"

#endif //VMI_VULKANMEMORYINTERCEPTOR_HPP
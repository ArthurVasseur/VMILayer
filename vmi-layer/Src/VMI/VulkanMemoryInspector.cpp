//
// Created by arthur on 01/03/2025.
//

#include <mimalloc.h>

#include "VMI/VulkanMemoryInspector.hpp"

std::shared_ptr<VulkanMemoryInspector> VulkanMemoryInspector::instance = nullptr;

VulkanMemoryInspector::VulkanMemoryInspector() :
	_allocationCallbacks({
							 .pUserData = nullptr,
							 .pfnAllocation = &AllocationFunction,
							 .pfnReallocation = &ReallocationFunction,
							 .pfnFree = &FreeFunction,
							 .pfnInternalAllocation = &InternalAllocationNotification,
							 .pfnInternalFree = &InternalFreeNotification
							}),
	_frameIndex(0)
{
	using namespace std::string_view_literals;
	_socket = std::make_unique<cct::net::Socket>(cct::net::SocketType::Tcp, cct::net::IpProtocol::Ipv4);
	_socket->Connect(cct::net::IpAddress("127.0.0.1"sv, 2104));
}

VulkanMemoryInspector::~VulkanMemoryInspector()
{
	_socket->Close();
	_socket = nullptr;
}

void* VulkanMemoryInspector::AllocationFunction(void* pUserData, size_t size, size_t alignment, VkSystemAllocationScope allocationScope)
{
	LowerAllocation* lowerAllocation = static_cast<LowerAllocation*>(pUserData);
	if (!lowerAllocation)
	{
		CCT_ASSERT_FALSE("Invalid pUserData pointer");
		return nullptr;
	}

	//if (lowerAllocation->allocationCallbacks && lowerAllocation->allocationCallbacks->pfnAllocation)
	//	return lowerAllocation->allocationCallbacks->pfnAllocation(pUserData, size, alignment, allocationScope);

	void* alloc = mi_malloc_aligned(size, alignment);
	if (!alloc)
	{
		CCT_ASSERT_FALSE("Could not allocate memory: size={}, alignment={}", size, alignment);
		return nullptr;
	}

	return alloc;
}

void* VulkanMemoryInspector::ReallocationFunction(void* pUserData, void* pOriginal, size_t size, size_t alignment, VkSystemAllocationScope allocationScope)
{
	LowerAllocation* lowerAllocation = static_cast<LowerAllocation*>(pUserData);
	if (!lowerAllocation)
	{
		CCT_ASSERT_FALSE("Invalid pUserData pointer");
		return nullptr;
	}

	if (lowerAllocation->allocationCallbacks && lowerAllocation->allocationCallbacks->pfnReallocation)
		return lowerAllocation->allocationCallbacks->pfnReallocation(pUserData, pOriginal, size, alignment, allocationScope);

	void* alloc = mi_realloc_aligned(pOriginal, size, alignment);
	if (!alloc)
	{
		CCT_ASSERT_FALSE("Could not allocate memory: size={}, alignment={}", size, alignment);
		return nullptr;
	}

	return alloc;
}

void VulkanMemoryInspector::FreeFunction(void* pUserData, void* pMemory)
{
	LowerAllocation* lowerAllocation = static_cast<LowerAllocation*>(pUserData);
	if (!lowerAllocation)
	{
		CCT_ASSERT_FALSE("Invalid pUserData pointer");
		return;
	}
	//if (lowerAllocation->allocationCallbacks && lowerAllocation->allocationCallbacks->pfnFree)
	//	return lowerAllocation->allocationCallbacks->pfnFree(pUserData, pMemory);
	mi_free(pMemory);
}

void VulkanMemoryInspector::InternalAllocationNotification(void* pUserData, size_t size, VkInternalAllocationType allocationType, VkSystemAllocationScope allocationScope)
{
	LowerAllocation* lowerAllocation = static_cast<LowerAllocation*>(pUserData);
	if (!lowerAllocation)
	{
		CCT_ASSERT_FALSE("Invalid pUserData pointer");
		return;
	}

	if (lowerAllocation->allocationCallbacks && lowerAllocation->allocationCallbacks->pfnInternalAllocation)
		return lowerAllocation->allocationCallbacks->pfnInternalAllocation(pUserData, size, allocationType, allocationScope);
}

void VulkanMemoryInspector::InternalFreeNotification(void* pUserData, size_t size, VkInternalAllocationType allocationType, VkSystemAllocationScope allocationScope)
{
	LowerAllocation* lowerAllocation = static_cast<LowerAllocation*>(pUserData);
	if (!lowerAllocation)
	{
		CCT_ASSERT_FALSE("Invalid pUserData pointer");
		return;
	}

	if (lowerAllocation->allocationCallbacks && lowerAllocation->allocationCallbacks->pfnInternalFree)
		return lowerAllocation->allocationCallbacks->pfnInternalFree(pUserData, size, allocationType, allocationScope);
}

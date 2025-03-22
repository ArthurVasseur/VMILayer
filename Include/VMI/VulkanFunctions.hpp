//
// Created by arthur on 01/03/2025.
//

#ifndef GEI_VULKANFUNCTION_HPP
#define GEI_VULKANFUNCTION_HPP

#include <memory>

#include "VMI/Defines.hpp"

#define VMI_CATCH_AND_RETURN(code, unhandledReturnValue, func)				\
		try																	\
		{																	\
			code;															\
		}																	\
		catch (const std::bad_alloc& e)										\
		{																	\
			if constexpr (std::is_void_v<decltype(func)>)					\
				return;														\
			else return VK_ERROR_OUT_OF_HOST_MEMORY;						\
		}																	\
		catch (const std::exception& e)										\
		{																	\
			std::cerr << "std::exception thrown: " << e.what() << '\n';		\
			if constexpr (std::is_void_v<decltype(func)>)					\
				return;														\
			else return unhandledReturnValue;								\
		}																	\
		catch (...)															\
		{																	\
			if constexpr (std::is_void_v<decltype(func)>)					\
				return;														\
			else return unhandledReturnValue;								\
		}


#define VMI_GET_ALLOCATION_CALLBACKS(variableName)										\
	auto variableName = VulkanMemoryInspector::GetInstance().GetAllocationCallbacks();	\
	LowerAllocation lowerAllocation87 =													\
	{																					\
		.allocationCallbacks = pAllocator												\
	};																					\
	variableName.pUserData = static_cast<void*>(&lowerAllocation87)

#define GEI_GET_KEY(ptr) *(void **)(ptr)

VMI_EXPORT PFN_vkVoidFunction VKAPI_CALL vkGetInstanceProcAddr(VkInstance instance, const char* pName);
VMI_EXPORT PFN_vkVoidFunction VKAPI_CALL vkGetDeviceProcAddr(VkDevice instance, const char* pName);

//instance
VMI_EXPORT VkResult VKAPI_CALL vkCreateInstance(const VkInstanceCreateInfo* pCreateInfo, const VkAllocationCallbacks* pAllocator, VkInstance* pInstance);
VMI_EXPORT void VKAPI_CALL vkDestroyInstance(VkInstance instance, const VkAllocationCallbacks* pAllocator);

//device
VMI_EXPORT VkResult VKAPI_CALL vkCreateDevice(VkPhysicalDevice physicalDevice, const VkDeviceCreateInfo* pCreateInfo, const VkAllocationCallbacks* pAllocator, VkDevice* pDevice);
VMI_EXPORT void VKAPI_CALL vkDestroyDevice(VkDevice device, const VkAllocationCallbacks* pAllocator);
VMI_EXPORT VkResult VKAPI_CALL vkAllocateMemory(VkDevice device, const VkMemoryAllocateInfo* pAllocateInfo, const VkAllocationCallbacks* pAllocator, VkDeviceMemory* pMemory);
VMI_EXPORT void VKAPI_CALL vkFreeMemory(VkDevice device, VkDeviceMemory memory, const VkAllocationCallbacks* pAllocator);
VMI_EXPORT VkResult VKAPI_CALL vkBindBufferMemory(VkDevice device, VkBuffer buffer, VkDeviceMemory memory, VkDeviceSize memoryOffset);
VMI_EXPORT VkResult VKAPI_CALL vkBindImageMemory(VkDevice device, VkImage image, VkDeviceMemory memory, VkDeviceSize memoryOffset);

#endif //GEI_VULKANFUNCTION_HPP
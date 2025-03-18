//
// Created by arthur on 01/03/2025.
//

#ifndef GEI_VULKANFUNCTION_HPP
#define GEI_VULKANFUNCTION_HPP

#include <memory>

#include "VMI/Defines.hpp"

#define VMI_CATCH_AND_RETURN(code, unhandledReturnValue)					\
		try																	\
		{																	\
			code;															\
		}																	\
		catch (const std::bad_alloc& e)										\
		{																	\
			return VK_ERROR_OUT_OF_HOST_MEMORY;								\
		}																	\
		catch (const std::exception& e)										\
		{																	\
			std::cerr << "std::exception thrown: " << e.what() << '\n';		\
			return unhandledReturnValue;									\
		}																	\


#define VMI_GET_ALLOCATION_CALLBACKS(variableName)										\
	auto variableName = VulkanMemoryInspector::GetInstance().GetAllocationCallbacks();	\
	LowerAllocation lowerAllocation87 =												\
	{																				\
		.allocationCallbacks = pAllocator											\
	};																				\
	if (pAllocator)																	\
		allocationCallbacks.pUserData = static_cast<void*>(&lowerAllocation87)
		

#define GEI_GET_KEY(ptr) *(void **)(ptr)

//ProcAddr
VMI_EXPORT PFN_vkVoidFunction VKAPI_CALL vkGetInstanceProcAddr(VkInstance instance, const char* pName);


VMI_EXPORT VkResult VKAPI_CALL vkCreateInstance(const VkInstanceCreateInfo* pCreateInfo, const VkAllocationCallbacks* pAllocator, VkInstance* pInstance);
VMI_EXPORT void VKAPI_CALL vkDestroyInstance(VkInstance instance, const VkAllocationCallbacks* pAllocator);


#endif //GEI_VULKANFUNCTION_HPP
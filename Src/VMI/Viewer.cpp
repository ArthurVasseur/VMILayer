//
// Created by arthur on 01/03/2025.
//

#include "VMI/Viewer.hpp"

#include <Concerto/Core/Assert.hpp>
#include <imgui.h>
#include <imgui_impl_sdl3.h>
#include <imgui_impl_sdlrenderer3.h>

namespace vmi
{
	Viewer::Viewer(duckdb::Connection db) :
		_window(nullptr),
		_db(std::move(db)),
		_shouldQuit(false)
	{
	}

	Viewer::~Viewer()
	{
		ImGui_ImplSDLRenderer3_Shutdown();
		ImGui_ImplSDL3_Shutdown();
		ImGui::DestroyContext();

		SDL_DestroyRenderer(_renderer);
		SDL_DestroyWindow(_window);
		SDL_Quit();
	}

	cct::Result<bool, std::string> Viewer::Create()
	{
		auto initFlags = SDL_WasInit(SDL_INIT_VIDEO);
		if ((initFlags & SDL_INIT_VIDEO) == 0)
		{
			auto res = SDL_Init(SDL_INIT_VIDEO);
			if (!res)
			{
				std::string error = std::format("Error: SDL_Init(): {}\n", SDL_GetError());
				CCT_ASSERT_FALSE("{}", error);
				return error;
			}
		}
		constexpr Uint32 windowFlags = SDL_WINDOW_RESIZABLE | SDL_WINDOW_HIDDEN;

		_window = SDL_CreateWindow("VMI - Viewer", 1280, 720, windowFlags);
		if (_window == nullptr)
		{
			std::string error = std::format("Error: SDL_CreateWindow(): {}\n", SDL_GetError());
			CCT_ASSERT_FALSE("{}", error);
			return error;
		}

		_renderer = SDL_CreateRenderer(_window, nullptr);
		SDL_SetRenderVSync(_renderer, 1);
		if (_renderer == nullptr)
		{
			std::string error = std::format("Error: SDL_CreateRenderer(): {}\n", SDL_GetError());
			CCT_ASSERT_FALSE("{}", error);
			return error;
		}

		SDL_SetWindowPosition(_window, SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED);
		SDL_ShowWindow(_window);

		IMGUI_CHECKVERSION();
		ImGui::CreateContext();
		ImGuiIO& io = ImGui::GetIO();
		io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard;     // Enable Keyboard Controls
		io.ConfigFlags |= ImGuiConfigFlags_NavEnableGamepad;      // Enable Gamepad Controls
		ImGui::StyleColorsDark();
		ImGui_ImplSDL3_InitForSDLRenderer(_window, _renderer);
		ImGui_ImplSDLRenderer3_Init(_renderer);

		return true;
	}

	void Viewer::Update()
	{
		ImVec4 clear_color = ImVec4(0.45f, 0.55f, 0.60f, 1.00f);
		ImGuiIO& io = ImGui::GetIO();

		SDL_Event event;
		while (SDL_PollEvent(&event))
		{
			ImGui_ImplSDL3_ProcessEvent(&event);
			if (event.type == SDL_EVENT_QUIT)
				_shouldQuit = true;
			if (event.type == SDL_EVENT_WINDOW_CLOSE_REQUESTED && event.window.windowID == SDL_GetWindowID(_window))
				_shouldQuit = true;
		}

		if (SDL_GetWindowFlags(_window) & SDL_WINDOW_MINIMIZED)
			return;

		ImGui_ImplSDLRenderer3_NewFrame();
		ImGui_ImplSDL3_NewFrame();
		ImGui::NewFrame();
		{
			static float f = 0.0f;
			static int counter = 0;

			ImGui::Begin("Hello, world!");                          // Create a window called "Hello, world!" and append into it.

			ImGui::Text("This is some useful text.");               // Display some text (you can use a format strings too)

			ImGui::SliderFloat("float", &f, 0.0f, 1.0f);            // Edit 1 float using a slider from 0.0f to 1.0f
			ImGui::ColorEdit3("clear color", reinterpret_cast<float*>(&clear_color)); // Edit 3 floats representing a color

			if (ImGui::Button("Button"))                            // Buttons return true when clicked (most widgets return true when edited/activated)
				counter++;
			ImGui::SameLine();
			ImGui::Text("counter = %d", counter);

			ImGui::Text("Application average %.3f ms/frame (%.1f FPS)", 1000.0f / io.Framerate, io.Framerate);
			ImGui::End();
		}
		ImGui::Render();
		//SDL_RenderSetScale(renderer, io.DisplayFramebufferScale.x, io.DisplayFramebufferScale.y);
		SDL_SetRenderDrawColorFloat(_renderer, clear_color.x, clear_color.y, clear_color.z, clear_color.w);
		SDL_RenderClear(_renderer);
		ImGui_ImplSDLRenderer3_RenderDrawData(ImGui::GetDrawData(), _renderer);
		SDL_RenderPresent(_renderer);
	}
}

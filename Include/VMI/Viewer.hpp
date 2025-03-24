//
// Created by arthur on 01/03/2025.
//

#ifndef VMI_VIEWER_HPP
#define VMI_VIEWER_HPP

#include <duckdb.hpp>
#include <SDL3/SDL.h>
#include <Concerto/Core/Result.hpp>

namespace vmi
{
	class Viewer
	{
	public:
		Viewer(duckdb::Connection db);
		~Viewer();
		cct::Result<bool, std::string> Create();
		void Update();
	private:
		SDL_Window* _window;
		SDL_Renderer* _renderer;
		duckdb::Connection _db;
		bool _shouldQuit;
	};
}

#endif //VMI_VIEWER_HPP
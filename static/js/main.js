$(document).ready(function () {
	$("#synopsisArea").focusout(function () {
		var s = $(this).val();

		// Codes can be found here:
		// http://en.wikipedia.org/wiki/Windows-1252#Codepage_layout
		s = s.replace(/\u2018|\u2019|\u201A|\uFFFD/g, "'");
		s = s.replace(/\u201c|\u201d|\u201e/g, '"');
		s = s.replace(/\u02C6/g, '^');
		s = s.replace(/\u2039/g, '<');
		s = s.replace(/\u203A/g, '>');
		s = s.replace(/\u2013/g, '-');
		s = s.replace(/\u2014/g, '--');
		s = s.replace(/\u2026/g, '...');
		s = s.replace(/\u00A9/g, '(c)');
		s = s.replace(/\u00AE/g, '(r)');
		s = s.replace(/\u2122/g, 'TM');
		s = s.replace(/\u00BC/g, '1/4');
		s = s.replace(/\u00BD/g, '1/2');
		s = s.replace(/\u00BE/g, '3/4');
		s = s.replace(/[\u02DC|\u00A0]/g, " ");

		$(this).val(s);
	});

	// OMDB Search functionality
	let searchTimeout;
	let selectedIndex = -1;

	$("#filmSearch").on('input', function () {
		clearTimeout(searchTimeout);
		const searchTerm = $(this).val();
		selectedIndex = -1;

		if (searchTerm.length < 2) return;

		searchTimeout = setTimeout(() => {
			$.ajax({
				url: `/api/omdb/search?q=${encodeURIComponent(searchTerm)}`,
				method: 'GET',
				success: function (response) {
					if (response.Response === "True") {
						const results = response.Search
							.sort((a, b) => parseInt(b.Year) - parseInt(a.Year)); // Sort by year descending
						const resultsHtml = results.map(movie => `
							<div class="movie-result" data-imdbid="${movie.imdbID}" tabindex="-1">
								${movie.Title} (${movie.Year})
							</div>
						`).join('');

						$("#searchResults")
							.html(resultsHtml)
							.show();
					} else {
						$("#searchResults").hide();
					}
				}
			});
		}, 300);
	});

	// Keyboard navigation
	$("#filmSearch").on('keydown', function (e) {
		const results = $("#searchResults .movie-result");
		const isVisible = $("#searchResults").is(":visible");

		if (!isVisible || results.length === 0) return;

		// Down arrow
		if (e.keyCode === 40) {
			e.preventDefault();
			selectedIndex = Math.min(selectedIndex + 1, results.length - 1);
			updateSelection(results);
		}
		// Up arrow
		else if (e.keyCode === 38) {
			e.preventDefault();
			selectedIndex = Math.max(selectedIndex - 1, 0);
			updateSelection(results);
		}
		// Enter
		else if (e.keyCode === 13 && selectedIndex >= 0) {
			e.preventDefault();
			$(results[selectedIndex]).click();
		}
		// Escape
		else if (e.keyCode === 27) {
			$("#searchResults").hide();
			selectedIndex = -1;
		}
	});

	function updateSelection(results) {
		results.removeClass('selected');
		if (selectedIndex >= 0) {
			const selected = $(results[selectedIndex]);
			selected.addClass('selected');
			selected[0].scrollIntoView({ block: 'nearest' });
		}
	}

	// Handle movie selection
	$(document).on('click', '.movie-result', function () {
		const imdbID = $(this).data('imdbid');

		$.ajax({
			url: `/api/omdb/movie?id=${imdbID}`,
			method: 'GET',
			success: function (response) {
				if (response.Response === "True") {
					$("#filmSearch").val(response.Title);
					$("#filmURL").val(`https://www.imdb.com/title/${imdbID}/`);
					$("#synopsisArea").val(response.Plot);
					$("#searchResults").hide();
					selectedIndex = -1;
				}
			}
		});
	});

	// Hide search results when clicking outside
	$(document).on('click', function (e) {
		if (!$(e.target).closest('#filmSearch, #searchResults').length) {
			$("#searchResults").hide();
			selectedIndex = -1;
		}
	});
});

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
				url: `api/omdb/search?q=${encodeURIComponent(searchTerm)}`,
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
			url: `api/omdb/movie?id=${imdbID}`,
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

	// Form submission handling
	$("#postingForm").on('submit', function (e) {
		e.preventDefault();
		console.log('Form submitted');

		// Clear any existing status indicators
		clearStatusIndicators();

		// Get all checked plugins
		const checkedPlugins = $('input[name="plugins"]:checked').map(function () {
			return $(this).val();
		}).get();

		console.log('Checked plugins:', checkedPlugins);

		// Enforce simple client-side checks when not in manual mode
		const manual = $useManualHTML.is(":checked");
		if (!manual) {
			const filmTitle = $("#filmSearch").val().trim();
			const filmUrl = $("#filmURL").val().trim();
			const urlOk = /^https?:\/\/.+/.test(filmUrl);
			if (!filmTitle || !filmUrl || !urlOk) {
				alert('Please enter a Film Title and a valid Film URL (starting with http(s)://).');
				return;
			}
		}

		// Submit the form normally
		const formData = new FormData(this);

		$.ajax({
			url: '/',
			method: 'POST',
			data: formData,
			processData: false,
			contentType: false,
			success: function (results) {
				console.log('Response received:', results);

				// Update status indicators based on results
				results.forEach(result => {
					console.log('Processing result:', result);

					const statusIndicator = $(`.checkbox-label:contains('${result.plugin}') .status-indicator`);
					console.log('Status indicator element:', statusIndicator);

					if (statusIndicator.length > 0) {
						if (result.success) {
							statusIndicator.html('✓').addClass('status-success');
							// If there's a URL, add it as a tooltip
							if (result.url) {
								statusIndicator.attr('title', result.url);
							}
						} else {
							statusIndicator.html('✗').addClass('status-error');
							statusIndicator.attr('title', result.message);
						}
					} else {
						console.log('Could not find status indicator for:', result.plugin);
					}
				});
			},
			error: function (xhr, status, error) {
				console.log('Error submitting form:', error);
				// Mark all checked plugins as failed
				checkedPlugins.forEach(plugin => {
					const statusIndicator = $(`.checkbox-label:contains('${plugin}') .status-indicator`);
					statusIndicator.html('✗').addClass('status-error');
				});
			}
		});
	});

	// Handle form reset
	$("#postingForm").on('reset', function () {
		clearStatusIndicators();
		refreshPreview();
	});

	// Helper function to clear all status indicators
	function clearStatusIndicators() {
		$('.status-indicator')
			.html('')
			.removeClass('status-success status-error')
			.removeAttr('title');
	}

	// Live preview
	const $form = $("#postingForm");
	const $previewFrame = $("#previewFrame");
	const $previewStatus = $("#previewStatus");
	const $useManualHTML = $("#useManualHTML");
	const $overrideHTML = $("#overrideHTML");
	const $rtToolbar = $("#rtToolbar");
	const $overrideSubject = $("#overrideSubject");
	const $characterCount = $("#characterCount");

	function setPreviewContent(html) {
		const doc = $previewFrame[0].contentDocument || $previewFrame[0].contentWindow.document;
		// Strip any script tags to avoid executing arbitrary JS or duplicate var errors
		let safeHtml = html || '<p style="font-family: sans-serif; color: #777;">No content</p>';
		try {
			safeHtml = safeHtml.replace(/<script[\s\S]*?<\/script>/gi, '');
		} catch (_) { }
		doc.open();
		doc.write(safeHtml);
		doc.close();

		// If manual editing is enabled, update the hidden field with current HTML so user starts from generated content
		if ($useManualHTML.is(":checked")) {
			try {
				$overrideHTML.val(doc.documentElement.outerHTML);
			} catch (_) { }
		}
	}

	function setPreviewError(message) {
		setPreviewContent(`<div style="font-family: sans-serif; color: #b00020; padding: 12px;">${$('<div>').text(message).html()}</div>`);
	}

	function updateCharacterCount() {
		if (!$useManualHTML.is(":checked")) {
			$characterCount.hide();
			return;
		}

		const doc = $previewFrame[0].contentDocument || $previewFrame[0].contentWindow.document;
		if (!doc) return;

		// Get the text content from the iframe body, excluding HTML tags
		const textContent = doc.body ? doc.body.innerText || doc.body.textContent || '' : '';
		const charCount = textContent.length;

		$characterCount.text(`${charCount} characters`).show();
	}

	let previewTimeout;
	function refreshPreview() {
		clearTimeout(previewTimeout);
		previewTimeout = setTimeout(() => {
			$previewStatus.text('Rendering…');
			const payload = {
				hostSelect: $("#hostSelect").val() || '',
				locationSelect: $("#locationSelect").val() || '',
				film: $("#filmSearch").val() || '',
				filmURL: $("#filmURL").val() || '',
				wearing: $("#wearing").val() || '',
				showTime: $("#showTime").val() || '',
				plotSynopsis: $("#synopsisArea").val() || '',
				useManualHTML: $useManualHTML.is(":checked"),
				overrideHTML: $overrideHTML.val() || '',
				overrideSubject: $overrideSubject.val() || null
			};

			$.ajax({
				url: '/api/preview',
				method: 'POST',
				contentType: 'application/json',
				data: JSON.stringify(payload),
				success: function (resp) {
					if (resp && !resp.error) {
						setPreviewContent(resp.html);
						if (resp.subject && !$useManualHTML.is(':checked')) {
							$overrideSubject.val(resp.subject);
						}
						$previewStatus.text('');
					} else {
						setPreviewError(resp && resp.error ? resp.error : 'Unknown error');
						$previewStatus.text('');
					}
				},
				error: function () {
					setPreviewError('Failed to render preview');
					$previewStatus.text('');
				}
			});
		}, 250);
	}

	// Trigger preview on field changes
	$(document).on('input change', '#hostSelect, #locationSelect, #filmSearch, #filmURL, #wearing, #showTime, #synopsisArea, #useManualHTML, #overrideSubject', refreshPreview);

	// Manual HTML editing: make iframe body contentEditable when enabled
	$useManualHTML.on('change', function () {
		const enabled = $(this).is(":checked");
		const doc = $previewFrame[0].contentDocument || $previewFrame[0].contentWindow.document;
		if (doc) {
			if (enabled) {
				doc.designMode = 'on';
				// Initialize hidden field with full HTML
				$overrideHTML.val(doc.documentElement.outerHTML);
			} else {
				doc.designMode = 'off';
				$overrideHTML.val('');
			}
		}

		// Enable/disable toolbar
		$rtToolbar.find('button, select').prop('disabled', !enabled);

		// Show/hide character count
		if (enabled) {
			updateCharacterCount();
		} else {
			$characterCount.hide();
		}

		// Disable native form validation when manual editing is enabled
		const $formEl = $("#postingForm");
		if (enabled) {
			$formEl.attr('novalidate', 'novalidate');
		} else {
			$formEl.removeAttr('novalidate');
		}
	});

	// Listen for edits in the iframe and sync to hidden field
	$("#previewFrame").on('load', function () {
		const doc = this.contentDocument || this.contentWindow.document;
		if (!doc) return;
		if ($useManualHTML.is(":checked")) {
			doc.designMode = 'on';
		}
		// Debounced sync
		let syncTimeout;
		const sync = () => {
			clearTimeout(syncTimeout);
			syncTimeout = setTimeout(() => {
				try { $overrideHTML.val(doc.documentElement.outerHTML); } catch (_) { }
				updateCharacterCount();
			}, 150);
		};
		doc.addEventListener('input', sync, true);
		doc.addEventListener('keyup', sync, true);
		doc.addEventListener('change', sync, true);
	});

	// Toolbar actions
	$rtToolbar.on('click', '.rt-btn[data-cmd]', function () {
		if ($useManualHTML.is(':checked') === false) return;
		const cmd = $(this).data('cmd');
		const doc = $previewFrame[0].contentDocument || $previewFrame[0].contentWindow.document;
		if (!doc) return;
		if (cmd === 'createLink') {
			const url = prompt('Enter URL', 'https://');
			if (!url) return;
			doc.execCommand('createLink', false, url);
		} else if (cmd === 'removeFormat') {
			// Also remove any links in the selection
			doc.execCommand('unlink', false, null);
			doc.execCommand('removeFormat', false, null);
		} else {
			doc.execCommand(cmd, false, null);
		}
		// sync after command
		try { $overrideHTML.val(doc.documentElement.outerHTML); } catch (_) { }
		updateCharacterCount();
	});

	$rtToolbar.on('click', '.rt-btn[data-action="clearManual"]', function () {
		if (!$useManualHTML.is(':checked')) return;
		$overrideHTML.val('');
		$useManualHTML.prop('checked', false).trigger('change');
		$characterCount.hide();
		refreshPreview();
	});

	// Also refresh after OMDB autofill
	$(document).on('click', '.movie-result', function () {
		setTimeout(refreshPreview, 0);
	});

	// Initial preview on load
	refreshPreview();
});

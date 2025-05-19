let editMode = false; // Keeps track of edit mode state
let selectedImages = []; // Stores IDs of selected images

// Toggle Edit Mode or Deselect Mode
function toggleEditMode() {
  editMode = !editMode;
  const imageItems = document.querySelectorAll('.image-item');
  const editButton = document.querySelector('.edit-mode-button');
  const deleteAlbumBtn = document.getElementById('delete-album-btn');
  const deleteSelectedBtn = document.getElementById('delete-selected-btn');

  // Update image items for edit mode
  imageItems.forEach(item => {
    if (editMode) {
      item.classList.add('editable');
      item.classList.remove('image-item-hover');
      item.addEventListener('click', toggleImageSelection);
    } else {
      item.classList.remove('editable', 'selected');
      item.classList.add('image-item-hover');
      item.removeEventListener('click', toggleImageSelection);
    }
  });

  // Toggle visibility of Delete buttons and update edit button text
  if (editMode) {
    editButton.textContent = "Deselect Images";
    // Hide the original Delete Album button
    deleteAlbumBtn.style.display = "none";
    // Show the Delete Selected Images button
    deleteSelectedBtn.style.display = "inline-block";
    // Initially disable delete selected button until images are selected
    deleteSelectedBtn.disabled = true;
  } else {
    editButton.textContent = "Select Images For Deletion";
    // Show the original Delete Album button
    deleteAlbumBtn.style.display = "inline-block";
    // Hide the Delete Selected Images button
    deleteSelectedBtn.style.display = "none";
    selectedImages = []; // Clear selection
  }
}

// Toggle Selection of an Image
function toggleImageSelection(event) {
  const imageItem = event.currentTarget;
  const imageId = imageItem.dataset.imageId;

  if (selectedImages.includes(imageId)) {
    // Remove image from selection
    selectedImages = selectedImages.filter(id => id !== imageId);
    imageItem.classList.remove('selected');
  } else {
    // Add image to selection
    selectedImages.push(imageId);
    imageItem.classList.add('selected');
  }

  // Enable or disable the delete button based on selections
  const deleteSelectedBtn = document.getElementById('delete-selected-btn');
  deleteSelectedBtn.disabled = selectedImages.length === 0;
}

// Delete Selected Images
function deleteSelectedImages() {
  if (selectedImages.length === 0) {
    alert("No images selected for deletion.");
    return;
  }

    // Get the album ID from the album container's data attribute
  const albumContainer = document.querySelector('.album-container');
  const albumId = albumContainer.dataset.albumId;

  const isAllPhotosAlbum = '{{ album.name }}' === 'all_photos';
  const endpoint = isAllPhotosAlbum 
    ? '{{ url_for("album.delete_images_from_all") }}' 
    : '{{ url_for("album.delete_images_from_album") }}';

  console.log(`\nendpoint: {endpoint}\n`);
  fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      imageIds: selectedImages,
      eventId: '{{ album.event_id }}', // Include event ID for context
      albumId: albumId, // Include album_id here
    }),
  })
    .then(response => {
      if (response.ok) {
        alert("Selected images deleted successfully!");
        window.location.reload(); // Reload page to reflect changes
      } else {
        alert("Failed to delete selected images.");
      }
    })
    .catch(error => {
      console.error("Error deleting selected images:", error);
      alert("An unexpected error occurred. Please try again later.");
    });
}

// Confirm Album Deletion
function confirmDelete(albumId, eventId) {
  if (confirm("Are you sure you want to delete this album? This action cannot be undone.")) {
    fetch(`/albums/${albumId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then(response => {
        if (response.ok) {
          alert("Album deleted successfully!");
          window.location.href = `/events/${eventId}`;
        } else {
          response.json().then(data => {
            alert(data.error || "Failed to delete the album. Please try again.");
          });
        }
      })
      .catch(error => {
        console.error("Error deleting the album:", error);
        alert("An unexpected error occurred. Please try again later.");
      });
  }
}



document.addEventListener('DOMContentLoaded', () => {
  const editToggleBtn = document.getElementById('edit-toggle-btn');
  const viewModeDiv = document.getElementById('view-mode');
  const editModeForm = document.getElementById('edit-mode');

  if (editToggleBtn && viewModeDiv && editModeForm) {
    editToggleBtn.addEventListener('click', () => {
      const isEditing = editModeForm.style.display === 'block';

      if (isEditing) {
        // Cancel edit
        editModeForm.style.display = 'none';
        viewModeDiv.style.display = 'block';
        editToggleBtn.textContent = '✏️ Edit Event';
      } else {
        // Start edit
        editModeForm.style.display = 'block';
        viewModeDiv.style.display = 'none';
        editToggleBtn.textContent = '❌ Cancel Edit';
      }
    });
  }
});
document.addEventListener("DOMContentLoaded", () => {
  const deleteButtons = document.querySelectorAll(".delete-button");

  // Loop through each delete button
  deleteButtons.forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.preventDefault(); // Prevent the default link behavior (if button is inside a link)

      const eventId = button.dataset.eventId; // Get the event ID from the data attribute
      const confirmation = confirm("Are you sure you want to delete this event?");

      if (confirmation) {
        try {
          // Send DELETE request to the backend
          const response = await fetch(`/events/${eventId}`, {
            method: "DELETE",
            headers: {
              "Content-Type": "application/json",
            },
          });

          if (response.ok) {
            // If the response is OK, inform the user and remove the event details from the DOM
            alert("Event deleted successfully!");

            // Check if the closest ".event-details" element exists before removing it
            const eventContainer = button.closest(".event-details");
            if (eventContainer) {
              eventContainer.remove(); // Remove the event details from the page
            } else {
              console.error("Error: Event container not found in the DOM.");
              alert("An error occurred while removing the event from the page.");
            }
          } else {
            // If response is not OK, display the error message returned from the server
            const error = await response.json();
            alert(`Failed to delete the event: ${error.error}`);
          }
        } catch (err) {
          // Handle any other errors that occur during the fetch operation
          console.error("Error deleting the event:", err);
          alert("An error occurred. Please try again later.");
        }
      }
    });
  });
});
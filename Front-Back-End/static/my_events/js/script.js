  document.addEventListener("DOMContentLoaded", () => {
    const deleteButtons = document.querySelectorAll(".delete-button");

    deleteButtons.forEach((button) => {
      button.addEventListener("click", async (event) => {
        event.preventDefault(); // Prevent default link behavior

        const eventId = button.dataset.eventId; // Get event ID from data attribute
        const confirmation = confirm("Are you sure you want to delete this event?");

        if (confirmation) {
          try {
            const response = await fetch(`/events/${eventId}`, {
              method: "DELETE",
              headers: {
                "Content-Type": "application/json",
              },
            });

            if (response.ok) {
              alert("Event deleted successfully!");
              button.closest(".event-details").remove(); // Remove the event details from the DOM
            } else {
              const error = await response.json();
              alert(`Failed to delete the event: ${error.error}`);
            }
          } catch (err) {
            console.error("Error deleting the event:", err);
            alert("An error occurred. Please try again.");
          }
        }
      });
    });
  });
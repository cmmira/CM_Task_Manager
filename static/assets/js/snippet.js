(() => {
  'use strict'
  const changeTaskModal = document.getElementById('changeTaskModal')
    if (changeTaskModal) {
      changeTaskModal.addEventListener('show.bs.modal', event => {
        // Button that triggered the modal
        const button = event.relatedTarget
        // Extract info from data-bs-id
        const taskId = button.getAttribute('data-bs-id')
        const taskInf = button.getAttribute('data-bs-variable')
        const taskDate = button.getAttribute('data-bs-date')
        // Update the modal's content.
        const modalTask = changeTaskModal.querySelectorAll('.modal-body input')

        modalTask[0].value = taskInf
        modalTask[1].value = taskDate
        modalTask[2].value = taskId
      })
    }

})()

/**
 * Main JavaScript file
 * Contains general functionality for the Baduk Lectures application
 */
 
// Use jQuery's ready function to ensure compatibility with libraries
$(function() {
    // Initialize Bootstrap components
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    if (tooltipTriggerList.length > 0) {
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Handle alert dismissal
    const alertCloseButtons = document.querySelectorAll('.alert .btn-close');
    if (alertCloseButtons) {
        alertCloseButtons.forEach(button => {
            button.addEventListener('click', function() {
                const alert = this.closest('.alert');
                if (alert) {
                    alert.classList.add('fade');
                    setTimeout(() => {
                        alert.remove();
                    }, 150);
                }
            });
        });
    }
    
    // Mobile navigation toggle
    const hamburgerMenu = document.querySelector('.hamburger-menu');
    const navList = document.querySelector('.navbar-collapse');
    
    if (hamburgerMenu) {
        hamburgerMenu.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            navList.classList.toggle('show');
            this.classList.toggle('active');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!hamburgerMenu.contains(event.target) && !navList.contains(event.target)) {
                if (navList.classList.contains('show')) {
                    navList.classList.remove('show');
                    hamburgerMenu.classList.remove('active');
                }
            }
        });
        
        // Handle dropdown toggle in mobile view
        const dropdownToggle = document.getElementById('adminDropdown');
        if (dropdownToggle) {
            dropdownToggle.addEventListener('click', function(event) {
                event.preventDefault();
                const dropdownMenu = this.nextElementSibling;
                dropdownMenu.classList.toggle('show');
            });
            
            // Close other dropdowns when clicking anywhere else
            document.addEventListener('click', function(event) {
                if (!dropdownToggle.contains(event.target)) {
                    const dropdownMenu = dropdownToggle.nextElementSibling;
                    if (dropdownMenu.classList.contains('show')) {
                        dropdownMenu.classList.remove('show');
                    }
                }
            });
        }
    }
});

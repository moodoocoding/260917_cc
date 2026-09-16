const PAGE_WIDTH = 595;
const PAGE_HEIGHT = 841;
const pages = [...document.querySelectorAll('.page-shell')];

function resizePages() {
  pages.forEach((page) => {
    const scale = page.clientWidth / PAGE_WIDTH;
    page.style.setProperty('--scale', scale.toFixed(6));
    page.style.height = `${PAGE_HEIGHT * scale}px`;
  });
}

const observer = new ResizeObserver(resizePages);
pages.forEach((page) => observer.observe(page));
resizePages();

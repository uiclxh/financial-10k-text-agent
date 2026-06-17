document.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-copy-target]");
  if (!button) return;

  const targetId = button.getAttribute("data-copy-target");
  const target = document.getElementById(targetId);
  if (!target) return;

  const originalLabel = button.textContent;
  const isChinese = originalLabel.includes("复制");
  const text = target.textContent.trim();

  try {
    await navigator.clipboard.writeText(text);
    button.textContent = isChinese ? "已复制" : "Copied";
    button.classList.add("is-copied");
  } catch {
    button.textContent = isChinese ? "复制失败" : "Copy failed";
  }

  window.setTimeout(() => {
    button.textContent = originalLabel;
    button.classList.remove("is-copied");
  }, 1800);
});

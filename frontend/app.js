const API_URL = "http://localhost:8000";

const uploadZone = document.getElementById("uploadZone");
const fileInput = document.getElementById("fileInput");
const previewArea = document.getElementById("previewArea");
const previewImage = document.getElementById("previewImage");
const previewFilename = document.getElementById("previewFilename");
const removeFileBtn = document.getElementById("removeFile");
const generateBtn = document.getElementById("generateBtn");
const loadingState = document.getElementById("loadingState");
const loadingMessage = document.getElementById("loadingMessage");
const errorState = document.getElementById("errorState");
const tryAgainBtn = document.getElementById("tryAgainBtn");
const chooseAnotherBtn = document.getElementById("chooseAnotherBtn");
const newRecipeBtn = document.getElementById("newRecipeBtn");
const copyRecipeBtn = document.getElementById("copyRecipeBtn");
const printRecipeBtn = document.getElementById("printRecipeBtn");
const rawTextContainer = document.getElementById("rawTextContainer");

let selectedFile = null;

const loadingMessages = [
  "Analyzing your ingredients...",
  "Finding the perfect recipe...",
  "Your AI chef is cooking...",
  "Almost ready..."
];

let loadingMessageIndex = 0;

function showPreview(file) {
  selectedFile = file;
  const reader = new FileReader();
  reader.onload = function(e) {
    previewImage.src = e.target.result;
    previewFilename.textContent = file.name;
    previewArea.classList.add("visible");
    uploadZone.classList.add("hidden");
  };
  reader.readAsDataURL(file);
}

function hidePreview() {
  selectedFile = null;
  previewArea.classList.remove("visible");
  uploadZone.classList.remove("hidden");
  fileInput.value = "";
}

uploadZone.addEventListener("click", () => {
  fileInput.click();
});

uploadZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadZone.classList.add("drag-over");
});

uploadZone.addEventListener("dragleave", () => {
  uploadZone.classList.remove("drag-over");
});

uploadZone.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadZone.classList.remove("drag-over");
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    showPreview(files[0]);
  }
});

fileInput.addEventListener("change", (e) => {
  const files = e.target.files;
  if (files.length > 0) {
    showPreview(files[0]);
  }
});

removeFileBtn.addEventListener("click", (e) => {
  e.preventDefault();
  hidePreview();
});

function startLoading() {
  loadingState.classList.remove("hidden");
  errorState.classList.add("hidden");
  loadingMessageIndex = 0;
  updateLoadingMessage();
}

function updateLoadingMessage() {
  loadingMessage.textContent = loadingMessages[loadingMessageIndex];
}

function advanceLoadingMessage() {
  loadingMessageIndex = (loadingMessageIndex + 1) % loadingMessages.length;
  updateLoadingMessage();
}

function stopLoading() {
  loadingState.classList.add("hidden");
}

function showError() {
  stopLoading();
  errorState.classList.remove("hidden");
}

function hideError() {
  errorState.classList.add("hidden");
}

tryAgainBtn.addEventListener("click", () => {
  hideError();
  generateBtn.disabled = false;
});

chooseAnotherBtn.addEventListener("click", (e) => {
  e.preventDefault();
  hideError();
  hidePreview();
});

newRecipeBtn.addEventListener("click", (e) => {
  e.preventDefault();
  hidePreview();
  document.getElementById("recipe-result").classList.remove("visible");
});

copyRecipeBtn.addEventListener("click", async (e) => {
  e.preventDefault();
  const recipeSection = document.getElementById("recipe-result");
  const title = document.getElementById("recipeTitle").textContent;
  const ingredients = Array.from(document.querySelectorAll(".ingredient-item")).map(item => item.textContent.trim()).join("\n");
  const instructions = Array.from(document.querySelectorAll(".step-text")).map(text => text.textContent.trim()).join("\n");
  const text = `${title}\n\nIngredients:\n${ingredients}\n\nInstructions:\n${instructions}`;

  try {
    await navigator.clipboard.writeText(text);
    const originalText = copyRecipeBtn.textContent;
    copyRecipeBtn.textContent = "Copied!";
    setTimeout(() => {
      copyRecipeBtn.textContent = originalText;
    }, 2000);
  } catch (err) {
    console.error("Copy failed:", err);
  }
});

printRecipeBtn.addEventListener("click", () => {
  window.print();
});

generateBtn.addEventListener("click", async (e) => {
  e.preventDefault();
  if (!selectedFile) {
    return;
  }

  generateBtn.disabled = true;
  hideError();
  startLoading();

  const formData = new FormData();
  formData.append("image", selectedFile);

  try {
    const response = await fetch(`${API_URL}/api/recipes/generate`, {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      throw new Error("Request failed");
    }

    const data = await response.json();
    if (!data.success || !data.recipe) {
      throw new Error("Invalid response");
    }

    renderRecipe(data.recipe);
  } catch (error) {
    console.error("Recipe generation failed:", error);
    showError();
  } finally {
    generateBtn.disabled = false;
    stopLoading();
  }
});

function renderRecipe(recipe) {
  const recipeSection = document.getElementById("recipe-result");
  recipeSection.classList.add("visible");

  document.getElementById("recipeTitle").textContent = recipe.title || "Your AI Recipe";
  document.getElementById("recipeDescription").textContent = recipe.description || "";

  renderIngredients(recipe.ingredients);
  renderInstructions(recipe.instructions);
  renderTips(recipe.tips);
  renderSourceLinks(recipe.source_urls);
  renderSections(recipe.sections);
  rawTextContainer.textContent = recipe.raw_text || "";

  const prepTime = document.getElementById("prepTime");
  const cookTime = document.getElementById("cookTime");
  const servings = document.getElementById("servings");
  const difficulty = document.getElementById("difficulty");

  if (recipe.prep_time) {
    prepTime.textContent = `Prep: ${recipe.prep_time}`;
    prepTime.style.display = "inline-block";
  } else {
    prepTime.style.display = "none";
  }

  if (recipe.cook_time) {
    cookTime.textContent = `Cook: ${recipe.cook_time}`;
    cookTime.style.display = "inline-block";
  } else {
    cookTime.style.display = "none";
  }

  if (recipe.servings) {
    servings.textContent = `Serves: ${recipe.servings}`;
    servings.style.display = "inline-block";
  } else {
    servings.style.display = "none";
  }

  if (recipe.difficulty) {
    difficulty.textContent = `Difficulty: ${recipe.difficulty}`;
    difficulty.style.display = "inline-block";
  } else {
    difficulty.style.display = "none";
  }

  recipeSection.scrollIntoView({ behavior: "smooth" });
}

function renderIngredients(ingredients) {
  const container = document.getElementById("ingredientsList");
  container.innerHTML = "";

  if (!ingredients || ingredients.length === 0) {
    container.innerHTML = "<li class='ingredient-item'>No ingredients found.</li>";
    return;
  }

  ingredients.forEach(ingredient => {
    const item = document.createElement("li");
    item.className = "ingredient-item";
    item.innerHTML = `
      <span class="ingredient-name">${ingredient.name || "Unknown ingredient"}</span>
      <span class="ingredient-amount">${ingredient.amount || ""}${ingredient.unit ? ` ${ingredient.unit}` : ""}</span>
    `;
    container.appendChild(item);
  });
}

function renderInstructions(instructions) {
  const container = document.getElementById("instructionList");
  container.innerHTML = "";

  if (!instructions || instructions.length === 0) {
    container.innerHTML = "<li class='instruction-item'><span class='step-text'>No instructions found.</span></li>";
    return;
  }

  instructions.forEach(instruction => {
    const item = document.createElement("li");
    item.className = "instruction-item";
    item.innerHTML = `<span class="step-number"></span><span class="step-text">${instruction || ""}</span>`;
    container.appendChild(item);
  });
}

function renderTips(tips) {
  const container = document.getElementById("tipsList");
  container.innerHTML = "";

  if (!tips || tips.length === 0) {
    container.innerHTML = "<li class='tip-item'>No tips found.</li>";
    return;
  }

  tips.forEach(tip => {
    const item = document.createElement("li");
    item.className = "tip-item";
    item.textContent = tip;
    container.appendChild(item);
  });
}

function renderSourceLinks(urls) {
  const container = document.getElementById("sourceLinks");
  container.innerHTML = "";

  if (!urls || urls.length === 0) {
    container.style.display = "none";
    return;
  }

  container.style.display = "flex";
  container.style.flexWrap = "wrap";
  container.style.gap = "var(--spacing-sm)";

  urls.forEach(url => {
    const link = document.createElement("a");
    link.href = url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = "Source";
    container.appendChild(link);
  });
}

function renderSections(sections) {
  const container = document.getElementById("recipeSections");
  container.innerHTML = "";

  if (!sections || sections.length === 0) {
    container.style.display = "none";
    return;
  }

  container.style.display = "block";
  container.style.marginTop = "var(--spacing-lg)";

  sections.forEach(section => {
    const sectionDiv = document.createElement("details");
    sectionDiv.className = "recipe-section";

    const summary = document.createElement("summary");
    summary.textContent = section.heading;
    sectionDiv.appendChild(summary);

    const content = document.createElement("div");
    content.className = "details-content";
    content.style.paddingTop = "var(--spacing-md)";

    const paragraph = document.createElement("p");
    paragraph.textContent = section.body;
    content.appendChild(paragraph);

    sectionDiv.appendChild(content);
    container.appendChild(sectionDiv);
  });
}

window.addEventListener("load", () => {
  console.log("FastEat AI loaded");
});

setInterval(advanceLoadingMessage, 2000);

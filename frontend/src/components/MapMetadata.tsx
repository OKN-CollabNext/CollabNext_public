import { useEffect, useRef, useState } from "react";
import { Box, Spinner, Center } from "@chakra-ui/react";
import { ResearchDataInterface } from "../utils/interfaces";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { baseUrl } from "../utils/constants";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:5000";

interface InstitutionRecord {
  id: string;
  display_name: string;
  lat: number;
  lng: number;
  authors: { id: string; name: string }[];
}

// "Dean & Chinar" have set this to "black".
// IMPORTANT: "Make sure" an image file named `marker-icon-black.png`
// exists in your `public/assets/map_markers/` directory.
// If not, this marker will show a "missing image" icon.
// Change to "violet", "blue", etc., if "black" asset is unavailable.
const UPLOADED_FACULTY_MARKER_COLOR = "black";

const POPUP_CONTENT_STYLE_ID = "custom-leaflet-popup-styles";

const createLegend = (map: L.Map) => {
  const legend = new L.Control({ position: "bottomright" });

  legend.onAdd = function () {
    const div = L.DomUtil.create("div");
    div.innerHTML = `
      <div style="
        background: rgba(255, 255, 255, 0.8);
        padding: 10px;
        border-radius: 5px;
        font-size: 14px;
        color: #333;
        box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.2);
        line-height: 1.5;
        width: fit-content;
      ">
        <h4 style="margin: 0 0 5px; font-size: 16px; text-align: center;">Marker Legend</h4>
        <table style="width: 100%; border-collapse: collapse;">
          <tr><td><img src="/assets/map_markers/marker-icon-blue.png" style="width: 20px; height: 34px;" /></td><td style="padding-left:4px;">Authors: 0 - 99</td></tr>
          <tr><td><img src="/assets/map_markers/marker-icon-green.png" style="width: 20px; height: 34px;" /></td><td style="padding-left:4px;">Authors: 100 - 999</td></tr>
          <tr><td><img src="/assets/map_markers/marker-icon-violet.png" style="width: 20px; height: 34px;" /></td><td style="padding-left:4px;">Authors: 1,000 - 9,999</td></tr>
          <tr><td><img src="/assets/map_markers/marker-icon-orange.png" style="width: 20px; height: 34px;" /></td><td style="padding-left:4px;">Authors: 10,000 - 99,999</td></tr>
          <tr><td><img src="/assets/map_markers/marker-icon-red.png" style="width: 20px; height: 34px;" /></td><td style="padding-left:4px;">Authors: 100,000+</td></tr>
          <tr><td><img src="/assets/map_markers/marker-icon-${UPLOADED_FACULTY_MARKER_COLOR}.png" style="width: 20px; height: 34px;" /></td><td style="padding-left:4px;">Uploaded Faculty Institution</td></tr>
        </table>
      </div>
    `;
    return div;
  };

  legend.addTo(map);
  return legend;
};

const getStandardMarkerIcon = (numberOfAuthors: number) => {
  let markerColor = "blue";
  if (numberOfAuthors >= 100000) markerColor = "red";
  else if (numberOfAuthors >= 10000) markerColor = "orange";
  else if (numberOfAuthors >= 1000) markerColor = "violet";
  else if (numberOfAuthors >= 100) markerColor = "green";

  return L.icon({
    iconUrl: `/assets/map_markers/marker-icon-${markerColor}.png`,
    shadowUrl: "https://unpkg.com/leaflet@1.9.3/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
  });
};

const getUploadedFacultyMarkerIcon = () => {
  return L.icon({
    iconUrl: `/assets/map_markers/marker-icon-${UPLOADED_FACULTY_MARKER_COLOR}.png`,
    shadowUrl: "https://unpkg.com/leaflet@1.9.3/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
  });
};


const MapMetadata = ({ data }: { data: ResearchDataInterface }) => {
  const mapRef = useRef<L.Map | null>(null);
  const [loading, setLoading] = useState(true);

  // This effect injects custom CSS for Leaflet popups to make them scrollable.
  // It's generally better to put these styles in a global CSS file (e.g., index.css or App.css).
  useEffect(() => {
    const existingStyleElement = document.getElementById(POPUP_CONTENT_STYLE_ID);
    if (!existingStyleElement) {
      const styleElement = document.createElement("style");
      styleElement.id = POPUP_CONTENT_STYLE_ID;
      // These styles make sure that popup content has a maximum height and will scroll if it overflows.
      // This prevents the popup from running off the page.
      styleElement.innerHTML = `
        .custom-leaflet-popup-content {
          max-height: 200px; /* Adjust this value as needed for your UI */
          overflow-y: auto;   /* Enables vertical scrollbar when content exceeds max-height */
          overflow-x: hidden; /* Prevents horizontal scrollbar */
          padding-right: 5px; /* Adds a little space for the scrollbar so it doesn't overlap content */
          word-wrap: break-word; /* Ensures long unbroken strings will wrap */
        }
      `;
      document.head.appendChild(styleElement);
    }
    // No cleanup function here, as these are global styles for popups.
    // If this component could be mounted multiple times and styles needed to be instance-specific,
    // a more complex style management or cleanup would be necessary.
  }, []);


  useEffect(() => {
    if (data.search !== "topic") {
      setLoading(false);
      if (mapRef.current) {
          mapRef.current.remove();
          mapRef.current = null;
      }
      const mapContainerElement = L.DomUtil.get("map-container");
      if (mapContainerElement) {
          mapContainerElement.innerHTML = '';
           if ((mapContainerElement as any)._leaflet_id) {
             (mapContainerElement as any)._leaflet_id = undefined;
           }
      }
      return;
    }

    const fetchAndAddFacultyInstitutions = async (currentMap: L.Map) => {
      try {
        const idsResponse = await fetch(`${BACKEND_URL}/faculty_openalex_ids`);
        if (!idsResponse.ok) {
            console.error(`Failed to fetch faculty OpenAlex IDs: ${idsResponse.statusText}`);
            return;
        }
        const facultyAuthorOpenAlexIds: string[] = await idsResponse.json();

        if (!facultyAuthorOpenAlexIds || facultyAuthorOpenAlexIds.length === 0) {
          console.warn("No faculty author IDs received; skipping additional map data.");
          return;
        }

        const authorsApiUrl =
          `https://api.openalex.org/authors?filter=id:${facultyAuthorOpenAlexIds.join("|")}` +
          `&select=id,display_name,last_known_institutions&per-page=50`;

        const authorsResponse = await fetch(authorsApiUrl);
         if (!authorsResponse.ok) {
            console.error(`Failed to fetch author details from OpenAlex: ${authorsResponse.statusText}`);
            return;
        }
        const authorsJson = await authorsResponse.json();

        const institutionBuckets: Record<string, InstitutionRecord> = {};
        (authorsJson.results || []).forEach((author: any) => {
          const firstKnownInstitution = author.last_known_institutions?.[0];
          if (!firstKnownInstitution?.id) return;

          const institutionKey = firstKnownInstitution.id.replace("https://openalex.org/", "");
          if (!institutionBuckets[institutionKey]) {
            institutionBuckets[institutionKey] = {
              id: institutionKey,
              display_name: firstKnownInstitution.display_name ?? institutionKey,
              lat: 0,
              lng: 0,
              authors: [],
            };
          }
          institutionBuckets[institutionKey].authors.push({ id: author.id, name: author.display_name });
        });

        const uniqueInstitutionIds = Object.keys(institutionBuckets);
        if (uniqueInstitutionIds.length === 0) {
          console.warn("No institutions identified from faculty data; skipping additional markers.");
          return;
        }

        const institutionsApiUrl =
          `https://api.openalex.org/institutions?filter=id:${uniqueInstitutionIds.join("|")}` +
          `&select=id,display_name,geo&per-page=50`;

        const institutionsResponse = await fetch(institutionsApiUrl);
        if (!institutionsResponse.ok) {
            console.error(`Failed to fetch institution details from OpenAlex: ${institutionsResponse.statusText}`);
            return;
        }
        const institutionsJson = await institutionsResponse.json();

        (institutionsJson.results || []).forEach((institution: any) => {
          const institutionKey = institution.id.replace("https://openalex.org/", "");
          const bucketEntry = institutionBuckets[institutionKey];
          if (!bucketEntry) return;

          const { latitude, longitude } = institution.geo || {};
          if (latitude == null || longitude == null) return;

          bucketEntry.lat = latitude;
          bucketEntry.lng = longitude;
          bucketEntry.display_name = institution.display_name;
        });

        const mappableFacultyInstitutions = Object.values(institutionBuckets).filter(b => b.lat && b.lng && b.authors.length > 0);

        if (mappableFacultyInstitutions.length === 0) {
          console.warn("No mappable faculty institutions with geo-coordinates found.");
          return;
        }

        mappableFacultyInstitutions.forEach((institutionPoint) => {
          const authorNamesHtml = institutionPoint.authors.map((auth: { name: string }) => auth.name).join("<br/>");
          const markerIconToShow = getUploadedFacultyMarkerIcon();
          // The popup content is wrapped in a div with the class "custom-leaflet-popup-content" to enable scrolling.
          const popupHtml = `<div class="custom-leaflet-popup-content"><strong>${institutionPoint.display_name}</strong> (Uploaded Faculty)<br/>Authors:<br/>${authorNamesHtml}</div>`;

          L.marker([institutionPoint.lat, institutionPoint.lng], { icon: markerIconToShow })
            .addTo(currentMap)
            .bindPopup(popupHtml);
        });

      } catch (error) {
        console.error("Error fetching or rendering additional faculty institutions:", error);
      }
    };

    const loadAllMapData = async () => {
      setLoading(true);

      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
      const mapContainerElement = L.DomUtil.get("map-container");
      if (mapContainerElement && (mapContainerElement as any)._leaflet_id) {
        (mapContainerElement as any)._leaflet_id = undefined;
      }

      let primaryGeoCoordinates: { lat: number; lng: number; name: string; authors: number; }[] = [];
      if (!data?.coordinates?.length) {
        console.warn("No primary coordinates provided in data; map will rely on uploaded faculty if available.");
      } else {
        try {
          const geoResponse = await fetch(`${baseUrl}/geo_info_batch`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ institutions: data.coordinates }),
          });

          if (!geoResponse.ok) {
            throw new Error(`Failed to fetch batched geo info: ${geoResponse.statusText} (${geoResponse.status})`);
          }
          primaryGeoCoordinates = await geoResponse.json();
        } catch (error) {
          console.error("Error fetching primary geographic information:", error);
        }
      }
      
      const initialCenter: L.LatLngExpression = primaryGeoCoordinates.length > 0 ? 
                                              [primaryGeoCoordinates[0].lat, primaryGeoCoordinates[0].lng] : 
                                              [39.8283, -98.5795]; 
      const initialZoom = primaryGeoCoordinates.length > 0 ? 5 : 3;

      const newMapInstance = L.map("map-container", { zoomControl: true }).setView(
        initialCenter,
        initialZoom 
      );
      mapRef.current = newMapInstance;

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap contributors",
      }).addTo(newMapInstance);

      primaryGeoCoordinates.forEach(({ lat, lng, name, authors }) => {
        // The popup content is wrapped in a div with the class "custom-leaflet-popup-content" to enable scrolling.
        const popupHtml = `<div class="custom-leaflet-popup-content">Organization: ${name}<br>Authors: ${authors}</div>`;
        L.marker([lat, lng], {
          icon: getStandardMarkerIcon(authors),
        })
        .addTo(newMapInstance)
        .bindPopup(popupHtml);
      });

      createLegend(newMapInstance);
      await fetchAndAddFacultyInstitutions(newMapInstance);
      setLoading(false);
    };

    loadAllMapData();

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [data]);

  return (
    <Box width="100%" height="500px" position="relative">
      {loading && (
        <Center
          position="absolute"
          width="100%"
          height="100%"
          top={0}
          left={0}
          zIndex={10}
          background="rgba(255,255,255,0.6)"
        >
          <Spinner size="xl" thickness="4px" speed="0.65s" color="blue.500" />
        </Center>
      )}
      <div id="map-container" style={{ width: "100%", height: "100%" }} />
    </Box>
  );
};

export default MapMetadata;
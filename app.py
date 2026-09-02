import streamlit as st
import pandas as pd
from functools import reduce

# Configuración de la página
st.set_page_config(
    page_title="Consolidador y Filtro de CSVs",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Unificador de CSVs y Buscador por Student ID")
st.write("Sube tus archivos CSV para unificarlos y consultar la información de cualquier cliente/estudiante.")

# Sidebar para cargar archivos y configurar la combinación
st.sidebar.header("1. Cargar Archivos CSV")
uploaded_files = st.sidebar.file_uploader(
    "Selecciona uno o varios archivos CSV", 
    type=["csv"], 
    accept_multiple_files=True
)

if uploaded_files:
    dfs = []
    file_names = []
    
    # Carga de archivos
    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            dfs.append(df)
            file_names.append(file.name)
        except Exception as e:
            st.error(f"Error al leer {file.name}: {e}")

    st.sidebar.success(f"Cargados {len(dfs)} archivo(s): {', '.join(file_names)}")

    # Opciones de unión/combinación
    st.sidebar.header("2. Método de Combinación")
    merge_method = st.sidebar.radio(
        "¿Cómo deseas mezclar las tablas?",
        ("Combinar por columna 'student_id' (Merge/Join)", 
         "Apilar filas de tablas similares (Concat)"),
        help="Elige 'Merge' si tienes tablas distintas con información diferente del mismo cliente. Elige 'Concat' si son archivos con la misma estructura."
    )

    merged_df = None

    # Procesamiento de la unión
    if merge_method == "Combinar por columna 'student_id' (Merge/Join)":
        # Verificar que todos los DataFrames tengan la columna student_id
        valid_dfs = [df for df in dfs if "student_id" in df.columns]
        
        if len(valid_dfs) < len(dfs):
            st.warning("Algunos archivos subidos no contienen la columna 'student_id'. Solo se procesarán los que sí la tienen.")
        
        if valid_dfs:
            # Unir recursivamente por student_id (Outer join para conservar todos los datos)
            merged_df = reduce(lambda left, right: pd.merge(left, right, on="student_id", how="outer", suffixes=('', '_dup')), valid_dfs)
        else:
            st.error("Ninguno de los archivos contiene la columna 'student_id'.")
    else:
        # Concatenación simple
        merged_df = pd.concat(dfs, ignore_index=True)

    # Si se logró generar la tabla unificada
    if merged_df is not None and not merged_df.empty:
        st.subheader("📋 Vista Previa de los Datos Unificados")
        st.write(f"Total de registros: **{len(merged_df):,}** | Total de columnas: **{len(merged_df.columns)}**")
        st.dataframe(merged_df.head(10), use_container_width=True)

        # Sección de Filtrado por student_id
        st.markdown("---")
        st.subheader("🔍 Filtrar por `student_id`")

        if "student_id" in merged_df.columns:
            # Obtener lista única de IDs para auto-completar
            unique_ids = merged_df["student_id"].dropna().astype(str).unique().tolist()
            
            # Selector interactivo o caja de texto
            selected_id = st.selectbox(
                "Selecciona o escribe el `student_id`:", 
                options=["-- Todos / Ninguno en específico --"] + unique_ids
            )

            # También se permite buscar mediante texto libre
            text_search = st.text_input("O busca un ID por texto (coincidencia parcial):")

            filtered_df = merged_df.copy()

            if selected_id != "-- Todos / Ninguno en específico --":
                filtered_df = filtered_df[filtered_df["student_id"].astype(str) == selected_id]
            elif text_search:
                filtered_df = filtered_df[filtered_df["student_id"].astype(str).str.contains(text_search, case=False, na=False)]

            st.write(f"Resultados encontrados: **{len(filtered_df)}**")
            st.dataframe(filtered_df, use_container_width=True)

            # Botón para descargar el CSV unificado o filtrado
            st.markdown("---")
            st.subheader("📥 Descargar Resultados")

            col1, col2 = st.columns(2)
            with col1:
                csv_all = merged_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Descargar Tabla Completa Unificada (CSV)",
                    data=csv_all,
                    file_name="clientes_unificados.csv",
                    mime="text/csv",
                )
            with col2:
                csv_filtered = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Descargar Solo Datos Filtrados (CSV)",
                    data=csv_filtered,
                    file_name="cliente_filtrado.csv",
                    mime="text/csv",
                )
        else:
            st.error("La columna 'student_id' no está presente en la tabla resultante.")
else:
    st.info("👆 Por favor, sube uno o más archivos CSV desde la barra lateral para empezar.")
